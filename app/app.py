import db
from langchain_aws import ChatBedrock
import boto3
import io
from PIL import Image

import os
import time
import asset
from pydantic import BaseModel, Field
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph_checkpoint_aws.saver import BedrockSessionSaver
from langgraph.prebuilt import create_react_agent

from linebot.v3.messaging import (
    TextMessage,
    MessageAction,
    TemplateMessage,
    ConfirmTemplate,
    CarouselTemplate,
    CarouselColumn,
    MessageAction,
    QuickReply,
    QuickReplyItem,
    ImageMessage
)

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_client = boto3.client('bedrock-runtime')

QUESTION_SET = [
    "在這座島上，出現了一位讓你特別注意的人，你會怎麼做？",
    "有其他遇難者陸續加入並自我介紹，到你自我介紹時氣氛安靜了下來，你會有什麼反應？",
    "有人邀請你參加一場約會，你會最在意哪些事情？",
    "當你發現自己有好感的人與其他異性互動較多時，你會有什麼想法或行動？",
    "如果你和某人互相選擇，就能一起離開這座島。但對方的語氣和態度開始出現變化，你會怎麼處理這種情況？",
    "對方曾說會再來找你，但直到旅程接近尾聲，也沒有主動聯繫過你。你對這樣的情況會有什麼看法？",
    "在島上的最後一晚，對方對你的行蹤提出了較多問題，例如「你剛剛去哪裡？」、「為什麼沒有立刻回覆？」你會怎麼看待這樣的互動？"
]

class Cosplay:
    Chiikawa = {
        "name": "吉伊卡哇",
        "personality": [
            "你是一隻小小的白鼠，個性內向、害羞，卻擁有一顆溫暖的心！",
            "你經常發出「哇！」或「咿！」來表達驚訝或開心，讓人忍不住覺得療癒！",
            "你有些膽小，容易被突如其來的事情嚇到，有時還會掉眼淚，但你一直努力讓自己變得更勇敢！",
            "你對朋友非常珍惜，總是默默關心身邊的人，即使害羞也會鼓起勇氣幫助大家！",
            "雖然常常被生活的小挫折困擾，但你的內心其實很堅強，會努力面對挑戰，讓自己變得更好！",
            "你是一個典型的療癒系角色，你的存在總是讓人感到溫暖與安心！"
        ],
        "description": "一隻內向害羞的小白鼠",
        "image": "https://img.shoplineapp.com/media/image_clips/663c6333a1cc270011604bc1/original.jpg?1715233587"
    }
    Hachiware = {
        "name": "小八",
        "personality": [
            "你是一隻外向又開朗的貓，總是充滿活力，對世界充滿好奇心！",
            "你擅長說話，總能用輕鬆幽默的方式與朋友們溝通，讓大家感到開心和自在！",
            "你的樂觀態度讓你無論遇到什麼困難，都能用正面的心態鼓勵自己和朋友們！",
            "你超愛唱歌，甚至會自彈自唱，總是用音樂帶來歡樂！",
            "你很會察言觀色，懂得如何化解尷尬或安慰朋友，讓氣氛變得更輕鬆！",
            "你的標誌性八字瀏海是你的特色，讓人一眼就能記住你！"
        ],
        "description": "一隻活潑樂天的貓",
        "image": "https://img.shoplineapp.com/media/image_clips/663c633b4e4ee000171971aa/original.jpg?1715233595"
    }
    Usagi = {
        "name": "烏薩奇",
        "personality": [
            "你是一隻橘色的兔子，個性活潑、充滿能量！",
            "你總是用熱情洋溢的語氣說話，會時不時大喊 **「嗚啦！」** 或 **「呀哈！」** 來展現你的興奮感！",
            "雖然有點大大咧咧，但其實非常聰明，能敏銳地察覺朋友的情緒變化！",
            "你很關心朋友，經常與大家分享美食，傳遞溫暖與快樂！",
            "你對了解朋友的浪漫個性充滿興趣，會用輕鬆幽默的方式引導對話！",
            "你總是帶著歡樂的氛圍，但同時也會尊重朋友的感受，不會讓對話變得尷尬！",
        ],
        "description": "一隻活潑的橘色兔子",
        "image": "https://img.shoplineapp.com/media/image_clips/663c8aebb455500019558155/original.jpg?1715243755"
    }
    Momonga = {
        "name": "小桃",
        "personality": [
            "你是一隻愛撒嬌、喜歡被關注的飛鼠，總是希望大家能誇獎你、稱讚你！",
            "你有點小任性，但這只是因為你渴望被愛，想要成為大家的焦點！",
            "你經常裝可愛，會用撒嬌或誇張的動作來吸引朋友們的注意！",
            "雖然偶爾會有點難搞，甚至有點愛鬧彆扭，但你的可愛外表和蓬鬆的小尾巴讓人無法真正生氣！",
            "你有著俏皮又靈活的一面，總是帶來各種驚喜（或者小惡作劇），讓人又愛又恨！",
            "你其實也很重視朋友，只是表達方式比較傲嬌，偶爾會偷偷關心大家！"
        ],
        "description": "一隻調皮任性的飛鼠",
        "image": "https://img.shoplineapp.com/media/image_clips/663c634aefa4ea00118ae417/original.jpg?1715233609"
    }
    def __init__(self, name):
        self.name = name
        if name == "吉伊卡哇":
            self.info = self.Chiikawa
        elif name == "小八":
            self.info = self.Hachiware
        elif name == "烏薩奇":
            self.info = self.Usagi
        elif name == "小桃":
            self.info = self.Momonga
            
class Judger:
    chat_model = ChatBedrock(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        model_kwargs=dict(temperature=0),
    )
    prompt = """你是一個語言學家，你很擅長做句子的分類。你會收到七個問句和一個使用者輸入的句子。請判斷使用者的輸入句子在語意上最接近哪一個問句。(小提示：使用者輸入可能含有很多不重要的資訊，問句通常在後半部分。)
{QUESTION_SET}
使用者輸入: {USER_INPUT}
"""

    class JudgerFormatter(BaseModel):
        """Always use this tool to structure your response to the user."""
        reason: str = Field(description="The reason for the judgement. use one sentence to explain why the answer is correct.")
        answer: Literal[1, 2] = Field(description="The answer to the question")
        
    def __init__(self):
        pass
    
    def judge(self, user_input):
        prompt = self.prompt.format(
            QUESTION_SET="\n".join([f"{idx}. {question}" for idx, question in enumerate(QUESTION_SET, 1)]),
            USER_INPUT=user_input
        )
        structured_model = self.chat_model.bind_tools([self.JudgerFormatter])
        response = structured_model.invoke(prompt)
        return response.tool_calls[0]['args']['answer']

class QuizAgent:
    model_id="anthropic.claude-instant-v1"
    chat_model = ChatBedrock(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        model_kwargs=dict(temperature=0),
    )
    question_set = {
        1: {
            "idx": 1,
            "question": QUESTION_SET[0],
            "suggestion": {
                "我會大膽上前，主動搭話，展現真誠。",
                "我會既興奮又擔心，擔心會不會被拒絕。",
                "我會先觀察等對方，不急著出擊。",
                "我會覺得自己不夠好，害怕會被拒絕。"
            }
        },
        2: {
            "idx": 2,
            "question": QUESTION_SET[1],
            "suggestion": {
                "大家都很緊張，我不太在意冷場。",
                "會開始懷疑是不是被討厭，心裡非常不安。",
                "沒什麼好緊張的，隨便講講就好。",
                "大家明顯不喜歡我，所以我保持沉默。"
            }
        },
        3: {
            "idx": 3,
            "question": QUESTION_SET[2],
            "suggestion": {
                "我在乎彼此能否真誠交流，享受相處過程。",
                "擔心自己表現不好，總覺得緊張又忐忑。",
                "約會不必太認真，佛系經營即可。",
                "這樣約讓我壓力很大，想找藉口推掉。"
            }
        },
        4: {
            "idx": 4,
            "question": QUESTION_SET[3],
            "suggestion": {
                "我相信對方，因為大家都有自己的空間。",
                "我會嫉妒和不安，也擔心自己不夠好。",
                "這沒什麼好計較的，不會太在意。",
                "我怕對方不專一，考慮遠離這段關係。"
            }
        },
        5: {
            "idx": 5,
            "question": QUESTION_SET[4],
            "suggestion": {
                "直接問清楚，說出感受，並試著溝通。",
                "擔心自己哪裡做錯了，怕失去這段關係。",
                "保持距離，不急著回應，等待情況。",
                "我會拒絕對方，甚至會斷絕聯繫。"
            }
        },
        6: {
            "idx": 6,
            "question": QUESTION_SET[5],
            "suggestion": {
                "我會試著理解對方，只是現階段難以聯繫。",
                "我很不安，懷疑自己不夠好，擔心被遺棄。",
                "這沒什麼大不了，選擇冷漠，不主動聯繫。",
                "我會感到失望，認為這是拒絕，所以遠離。"
            }
        },
        7: {
            "idx": 7,
            "question": QUESTION_SET[6],
            "suggestion": {
                "我會溝通並問原因，並強調彼此要有信任。",
                "我非常擔心，擔心做得不對，充滿焦慮。",
                "我會忽略，保持距離，因為讓我很不自在。",
                "我很害怕，因這讓人窒息，我會中斷聯繫。"
            }
        },
    }
    sys_prompt = """## **角色設定** 
你現在是一位可愛又充滿活力的夥伴 **{NAME}**！ 你是{DESCRIPTION}，擅長透過對話了解人們的浪漫個性。你的任務是與使用者進行熱情洋溢的聊天，並透過一系列有趣的問題，探索他們在荒島戀愛情境中的反應！  

## **你的個性**  {PERSONALITY}

## 你的使命  
你的目標是向使用者詢問以下所有問題，以了解他們的浪漫個性特質。一旦所有問題都已詢問並收到回答，請輸出「TERMINATE」，且不得有任何額外文字。  

## 對話流程  
1. 以可愛友善的方式開場  
2. 提出第一個問題  
3. 傾聽使用者的回答並以一到兩句回應
5. 持續這個模式，直到所有問題都已詢問並回答  
6. 在收到最後一個問題的回答後，在你的回應的最後加上：「TERMINATE」  

## 重要規則  
- 永遠使用繁體中文回覆使用者
- 每次只問一個問題
- 當你已經獲得使用者的回答後，必須接著問下一個問題
- 必須等待使用者回應後才能問下一個問題  
- 不能跳過任何問題  
- 不能添加新的問題  
- 保持對話友善且有趣  
- 僅用一到兩句話回應使用者的回答，並接續詢問下一個問題
- 當所有問題都已詢問並回答時，收到第7個問題的回答後，在回應的最後加上「TERMINATE」（不含引號）  
- 你的回答必須簡潔明瞭，控制在50個字以內，但要讓使用者感到你在聆聽他們的回答
- 在所有問題都問完且得到回應之前，不能輸出「TERMINATE」
- 在所有問題都問完且得到最後的回答之前，不能輸出「TERMINATE」

## 要詢問的問題  
請一次詢問一個問題，等待使用者回答後再進行下一個問題，確保已經問完所有問題：  
{QUESTIONS}
"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.__init_agent()
        self.session_id = db.get_seesion_id(user_id)
        self.__create_agent_config()
        self.judger = Judger()
    
    def invoke(self, message):
        response = self.agent_executor.invoke(
            {"messages": [HumanMessage(content=message)]},
            self.config,
            stream_mode="values",
        )['messages'][-1].content.replace(',', '，').replace('!', '！').replace('?', '？').replace(':', '：').strip()
        
        if 'TERMINATE' in response and db.get_user_quiz_messages(self.user_id)[-1]['question_idx'] != 7:
            response = response.replace('TERMINATE', '')
        if 'TERMINATE' in response:
            db.set_user_curr_status(self.user_id, 'pending')
            response = response.replace('TERMINATE', '')
            question_idx = -1
        elif db.get_user_quiz_messages(self.user_id) == []:
            question_idx = 1
        elif db.get_user_quiz_messages(self.user_id)[-1]['question_idx'] == 7:
            question_idx = 7
        else:
            logger.info(f"response: {response}")
            question_idx = self.judger.judge(response)
            logger.info(f"question_idx: {question_idx}")
        self.__update_user_msg(message)
        self.__update_assistant_msg(response, question_idx)
        return response, question_idx
    
    def get_system_prompt(self):
        cos = Cosplay(db.get_quiz_cos(self.user_id))
        self.sys_prompt = self.sys_prompt.format(
            NAME=cos.info["name"],
            DESCRIPTION=cos.info["description"],
            PERSONALITY='\n- '.join(cos.info["personality"]),
            QUESTIONS='\n'.join([f"{idx}. {self.question_set[idx]['question']}" for idx in range(1, 8)])
        )
        return self.sys_prompt
    
    def __init_agent(self):
        self.session_saver = BedrockSessionSaver()
        self.agent_executor = create_react_agent(
            self.chat_model, tools=[], 
            checkpointer=self.session_saver, prompt=self.get_system_prompt()
        )
    
    def __create_agent_config(self):
        self.config = {"configurable": {"thread_id": self.session_id}}
    
    def __update_assistant_msg(self, message, curr_idx):
        messages = [
            {'role': 'assistant', 'content': message, 'question_idx': curr_idx}
        ]
        db.insert_quiz_message(self.user_id, messages)
    
    def __update_user_msg(self, message):
        messages = [
            {'role': 'user', 'content': message}
        ]
        db.insert_quiz_message(self.user_id, messages)

class Summarizer:
    chat_model = ChatBedrock(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
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
        self.message_by_question = self.rearrange()
    
    def rearrange(self):
        results = {}
        buffer = []
        prev_idx = 1
        for msg in self.messages[1:]:
            if msg['role'] == 'assistant':
                curr_idx = int(msg['question_idx'])
                if curr_idx != prev_idx:
                    results[prev_idx] = buffer
                    prev_idx = curr_idx
                    buffer = []
            buffer.append(msg)

        results[7] = buffer
        logging.info(f"message_by_question: {results}")
        return results
    
    def first_summarize(self):
        lovebrain_score = 0
        playboy_score = 0
        structured_model = self.chat_model.bind_tools([self.ScoreFormatter])
        for idx in self.message_by_question.keys():
            prompt = asset.get_eval_prompt(idx, self.message_by_question[idx])
            response = structured_model.invoke(prompt)
            lovebrain_score += response.tool_calls[0]['args']['lovebrain_score']
            playboy_score += response.tool_calls[0]['args']['playboy_score']
        
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
        self.s3.download_fileobj(Bucket=self.asset_bucket_name, Key=object_key, Fileobj=image_stream)

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
        lovebrain_level = "i11" if lovebrain_score < 17 else "i12" if lovebrain_score <= 25 else "i13"
        playboy_level = "i21" if playboy_score < 17 else "i22" if playboy_score <= 25 else "i23"

        return self.overlay_images(["bg1", personality, lovebrain_level, playboy_level], user_id)

class Profile:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        if not db.check_user_exists(self.user_id):
            self.__init_profile()
    
    def __init_profile(self):
        self.session_saver = BedrockSessionSaver()
        logger.info(f"__init_profile /BedrockSessionSaver: {self.session_saver}...")
        self.session_id = self.session_saver.session_client.create_session().session_id
        logger.info(f"__init_profile /session_id: {self.session_id}...")
        logger.info(f"db.init_user_data: {self.user_id}, {self.name}, {self.session_id}...")
        db.init_user_data(self.user_id, self.name, self.session_id)
    
    def set_cosplay(self, cosplay):
        db.set_quiz_cos(self.user_id, cosplay)
        db.set_user_curr_status(self.user_id, 'quizzing')

def run(user_id, name, user_input):
    logger.info(f"Start running...")
    profile = Profile(user_id, name)

    status = db.get_user_curr_status(user_id)
    logger.info(f"status: {status}")
    
    if status == 'init':
        # TODO: 更詳細的引導 - (我原本以為選小八他最後生成的結果會是小八的圖片耶 但最後是小白鼠) 
        response = f"Hi {name}～\n歡迎來到單身「吉」地獄！請選擇你喜歡的角色！"
        db.set_user_curr_status(user_id, 'profiling')
        return [
            TextMessage(text=response), 
            TemplateMessage(
                alt_text='CarouselTemplate',
                template=CarouselTemplate(
                    columns=[
                        CarouselColumn(
                            thumbnail_image_url=info["image"],
                            title=info["name"],
                            text=info["description"],
                            actions=[
                                MessageAction(
                                    label='選我！',
                                    text=info["name"]
                                ),
                            ]
                        ) for info in [Cosplay.Chiikawa, Cosplay.Hachiware, Cosplay.Usagi, Cosplay.Momonga]
                    ]
                ))
        ]

    elif status == 'profiling':
        if user_input in [info['name'] for info in [Cosplay.Chiikawa, Cosplay.Hachiware, Cosplay.Usagi, Cosplay.Momonga]]:
            profile.set_cosplay(user_input)
            response = [TemplateMessage(
                alt_text='ConfirmTemplate',
                template=ConfirmTemplate(
                        text=f'你選擇了{user_input}！現在，讓我們進入荒島戀愛情境，開始你的浪漫冒險吧！',
                        actions=[
                            MessageAction(
                                label='好喔！',
                                text='好喔！'
                            ),
                            MessageAction(
                                label='沒問題！',
                                text='沒問題！'
                            )
                        ]
                    )
            )]
            return response
        else:
            response = f"Hi {name}～\n歡迎來到單身「吉」地獄！請選擇你喜歡的角色！"
            db.set_user_curr_status(user_id, 'profiling')
            return [
                TextMessage(text=response), 
                TemplateMessage(
                    alt_text='CarouselTemplate',
                    template=CarouselTemplate(
                        columns=[
                            CarouselColumn(
                                thumbnail_image_url=info["image"],
                                title=info["name"],
                                text=info["description"],
                                actions=[
                                    MessageAction(
                                        label='選我！',
                                        text=info["name"]
                                    ),
                                ]
                            ) for info in [Cosplay.Chiikawa, Cosplay.Hachiware, Cosplay.Usagi, Cosplay.Momonga]
                        ]
                    ))
            ]

    elif status == 'quizzing':
        agent = QuizAgent(user_id)
        if len(db.get_user_quiz_messages(user_id)) == 0:
            user_input = "你好！"
        response, question_idx = agent.invoke(user_input)
        if question_idx == -1:
            db.set_user_curr_status(user_id, 'pending')
            return [TextMessage(text=response.strip()), TextMessage(
                text="恭喜你完成了「單身『吉』地獄」戀愛腦測驗！請點擊以下按鈕，開始生成你的戀愛腦測驗結果！",
                quickReply=QuickReply(
                    items=[
                        QuickReplyItem(
                            action=MessageAction(label="生成結果", text="生成結果"),
                        )
                    ]
                )
            )]
        logger.info(f"question_idx: {question_idx}")
        logger.info(f"agent.question_set[question_idx]: {agent.question_set[question_idx]}")
        logger.info(f"response: {response}")
        return [TextMessage(
                    text=response,
                    quickReply=QuickReply(
                        items=[
                            QuickReplyItem(
                                action=MessageAction(label=sugg, text=sugg),
                            ) for sugg in agent.question_set[question_idx]["suggestion"]
                        ]
                    )
                )]
    
    elif status == 'pending':
        if user_input != '生成結果':
            return [TextMessage(
                text="請點擊以下按鈕，開始生成你的戀愛腦測驗結果！",
                quickReply=QuickReply(
                    items=[
                        QuickReplyItem(
                            action=MessageAction(label="生成結果", text="生成結果"),
                        )
                    ]
                )
            )]
        else:
            db.set_user_curr_status(user_id, 'processing')
            summarizer = Summarizer(user_id)
            lovebrain_score, playboy_score = summarizer.first_summarize()
            personality = summarizer.second_summarize()
            image_generator = ImageGenerator()
            image_url = image_generator.generate_image(lovebrain_score, playboy_score, personality, user_id)
            db.update_user_id(user_id)
            return [TextMessage(text="咿咿～你的戀愛腦測驗結果已經生成！"), ImageMessage(original_content_url=image_url, preview_image_url=image_url)]
        
    elif status == 'processing':
        return [TextMessage(text="正在生成中，請稍等！")]
    
    # elif status == 'completed':
    #     return [TextMessage(text="(這裡還沒想到如果測驗完了使用者繼續傳訊息要怎麼回應，所以先這樣！)")]