import db
from langchain_aws import ChatBedrock
import boto3
import io
from PIL import Image
import logging

import os
import time
import asset
from pydantic import BaseModel, Field
from typing import Literal
from langchain.tools import StructuredTool, tool

from langchain_core.messages import HumanMessage
from langgraph_checkpoint_aws.saver import BedrockSessionSaver
from langgraph.prebuilt import create_react_agent

model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Summarizer:
    chat_model = ChatBedrock(
        model_id=model_id,
        model_kwargs=dict(temperature=0),
    )
    class ScoreFormatter(BaseModel):
        """Always use this tool to structure your response to the user."""
        playboy_score: Literal[1, 2, 3, 4 ,5] = Field(description="The score of the playboy level of the friend B")
        lovebrain_score: Literal[1, 2, 3, 4 ,5] = Field(description="The score of the lovebrain level of the friend B")
    
    class PersonalityFormatter(BaseModel):
        """Always use this tool to structure your response to the user."""
        personality: Literal["A", "B", "C", "D"] = Field(description="The personality of the friend B")
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.messages = db.get_user_quiz_messages(self.user_id)
    
    def first_summarize(self):
        lovebrain_score = 0
        playboy_score = 0
        structured_model = self.chat_model.bind_tools([self.ScoreFormatter])
        prompt = asset.get_eval_prompt(self.messages)
        response = structured_model.invoke(prompt)
        lovebrain_score = response.tool_calls[0]['args']['lovebrain_score']
        playboy_score = response.tool_calls[0]['args']['playboy_score']
        
        return lovebrain_score, playboy_score
    
    def second_summarize(self):
        structured_model = self.chat_model.bind_tools([self.PersonalityFormatter])
        prompt = asset.get_classify_personality_prompt(self.messages)
        response = structured_model.invoke(prompt)
        return response.tool_calls[0]['args']['personality']


class ImageGenerator:
    def __init__(self):
        self.s3 = boto3.client('s3')
        self.asset_bucket_name = os.getenv('ASSET_BUCKET_NAME')
        self.output_bucket_name = os.getenv('OUTPUT_BUCKET_NAME')
        
    def get_image_from_s3(self, object_key):
        # Download image from S3 into memory
        image_stream = io.BytesIO()
        self.s3.download_fileobj(
            Bucket=self.asset_bucket_name,
            Key=object_key,
            Fileobj=image_stream
        )

        # Move the stream position to the start
        image_stream.seek(0)

        return Image.open(image_stream).convert("RGBA")
    
    def overlay_images(self, img_paths, user_id):
        base = self.get_image_from_s3(f"asset/{img_paths[0]}.png")

        for path in img_paths[1:]:
            overlay = self.get_image_from_s3(f"asset/{path}.png")
            base = Image.alpha_composite(base, overlay)

        img_byte_arr = io.BytesIO()
        base.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        filename = f"{user_id}.png"
        self.s3.upload_fileobj(img_byte_arr, self.output_bucket_name, filename, ExtraArgs={
            'ContentType': 'image/png',
        })

        url = f"https://{self.output_bucket_name}.s3.amazonaws.com/{filename}"
        return url
    
    def generate_image(self, lovebrain_score, playboy_score, personality, user_id):
        personality_map = {
            'A': 'c1',
            'B': 'c2',
            'C': 'c3',
            'D': 'c4'
        }
        personality = personality_map[personality]
        lovebrain_level = "i11" if lovebrain_score <= 2  else "i12" if lovebrain_score == 3 else "i13"
        playboy_level = "i21" if playboy_score <= 2 else "i22" if playboy_score == 3 else "i23"

        return self.overlay_images(["bg1", personality, lovebrain_level, playboy_level], user_id)
    
def get_quiz_result(user_id):
    db.set_user_curr_status(user_id, 'processing')
    summarizer = Summarizer(user_id)
    lovebrain_score, playboy_score = summarizer.first_summarize()
    logger.info(f"lovebrain_score {lovebrain_score}, playboy_score {playboy_score}")
    personality = summarizer.second_summarize()
    logger.info(f"personality {personality}")

    image_generator = ImageGenerator()
    image_url = image_generator.generate_image(lovebrain_score, playboy_score, personality, user_id)
    logger.info(f"image_url {image_url}")
    return image_url