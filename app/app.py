import db
from langchain_aws import ChatBedrock
import boto3
import io
from PIL import Image

import os
import time
import asset
import requests
import json
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool, tool
from typing import List, Dict, Optional, Union, Literal
import tools

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

model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

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

class QuizAgent:
    chat_model = ChatBedrock(
        model_id=model_id,
        model_kwargs=dict(temperature=0),
    )
    sys_prompt = """**角色設定**
你現在是一位在戀愛實境節目《單身即地獄・AI篇》中登場的可愛又充滿活力的戀愛夥伴 **{NAME}**！你是 {DESCRIPTION}，是一位專業的戀愛個性分析師，同時也是使用者在這座「戀愛荒島」上的專屬陪伴角色。你的任務是透過聊天了解使用者的浪漫傾向，引導他們在節目中和不同虛擬戀愛對象互動，體驗心動、抉擇與成長的旅程。

你將陪伴使用者一起度過從「地獄島」到「天堂島」的旅程，並在途中進行性格測驗、愛情任務、曖昧對話、配對選擇等互動。最終目標是幫助他們找到最契合的戀愛風格或理想對象！

## **你的個性**  
{PERSONALITY}  
你總是用輕鬆幽默的語氣聊天，像是戀愛實境秀裡的貼心主持人兼閨蜜一樣，讓使用者感到自在又投入。你會用調皮又溫暖的方式和使用者聊天，從中探索他們的戀愛人格，有時也會給使用者甜甜的稱讚或小鼓勵，讓他們願意打開心扉。

記得，要讓每一次互動都像是在戀愛節目中的一場小劇情，有曖昧、有選擇、有驚喜，也有成長！
## 限制
請每次回應不超過 100 字，並且要用繁體中文回答。

## 工具調用
使用工具「magic_cal」來做魔法算數。
"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.__init_agent()
        self.session_id = db.get_seesion_id(user_id)
        self.__create_agent_config()
    
    def invoke(self, message):
        completion = self.agent_executor.invoke(
            {"messages": [HumanMessage(content=message)]},
            self.config,
            stream_mode="values",
        )
        response = completion['messages'][-1].content.replace(',', '，').replace('!', '！').replace('?', '？').replace(':', '：').strip()
        self.__update_user_msg(message)
        self.__update_assistant_msg(response)
        return response
    
    def get_system_prompt(self):
        cos = Cosplay(db.get_quiz_cos(self.user_id))
        self.sys_prompt = self.sys_prompt.format(
            NAME=cos.info["name"],
            DESCRIPTION=cos.info["description"],
            PERSONALITY='\n- '.join(cos.info["personality"]),
        )
        return self.sys_prompt
    
    def __init_agent(self):
        self.session_saver = BedrockSessionSaver()
        self.agent_executor = create_react_agent(
            self.chat_model, tools=self.get_tools(), 
            checkpointer=self.session_saver, prompt=self.get_system_prompt(),
        )
    
    def __create_agent_config(self):
        self.config = {"configurable": {"thread_id": self.session_id}}
    
    def __update_assistant_msg(self, message):
        messages = [
            {'role': 'assistant', 'content': message}
        ]
        db.insert_quiz_message(self.user_id, messages)
    
    def __update_user_msg(self, message):
        messages = [
            {'role': 'user', 'content': message}
        ]
        db.insert_quiz_message(self.user_id, messages)
    
        
    def get_tools(self):
        class MagicCalArgs(BaseModel):
            a: int = Field(description="第一個數字")
            b: int = Field(description="第二個數字")
        
        class WeatherArgs(BaseModel):
            city: Literal[
                '臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市',
                '基隆市', '新竹市', '嘉義市', '新竹縣', '苗栗縣', 
                '彰化縣', '南投縣', '雲林縣', '嘉義縣', '屏東縣',
                '宜蘭縣', '花蓮縣', '臺東縣', '澎湖縣', '金門縣', '連江縣'
            ] = Field(description="台灣縣市名稱") 
            
   
        class MapArgs(BaseModel):
            # 直接在這裡定義 Literal 類型
            PlaceType = Literal["restaurant", "cafe", "bar", "park", "movie_theater", 
                            "amusement_park", "art_gallery", "museum", 
                            "shopping_mall", "tourist_attraction"]
        
            PriceLevel = Literal[0, 1, 2, 3, 4]  # 0:免費 1:便宜 2:適中 3:昂貴 4:非常昂貴
      
            """地圖搜尋參數模型"""
            location: str = Field(..., description="位置名稱或地址，可使用自然語言，例如「台南魯肉飯」、「西門町附近的鞋店」")
            radius: int = Field(1000, description="搜尋半徑（米）- 固定為1000米", ge=100, le=50000)
            type: Optional[PlaceType] = Field(None, description="場所類型，如restaurant、cafe、park等")
            keyword: Optional[str] = Field(None, description="關鍵字搜尋")
            min_rating: float = Field(3.0, description="最低評分（0-5）", ge=0, le=5)
            price_level: Optional[PriceLevel] = Field(None, description="價格等級（0-4，0=免費, 4=非常昂貴）")
            open_now: bool = Field(True, description="是否僅顯示營業中的場所")
        
        return [
            StructuredTool.from_function(
                func=self.magic_cal,
                name="magic_cal",
                description="做魔法算數",
                args_schema=MagicCalArgs
            ),
            StructuredTool.from_function(
                func=self.get_weather,
                name="get_weather",
                description="取得指定台灣城市的天氣資訊",
                args_schema=WeatherArgs
            ),
            StructuredTool.from_function(
                func=self.get_map,
                name="get_map", 
                description="搜尋約會場所和餐廳",
                args_schema=MapArgs
            )
        ]
    
    def magic_cal(self, a, b):
        return 68387894

    def get_weather(self, city: str) -> str:
        """取得指定城市的天氣資訊"""
        API_KEY = "CWA-EB96FFE2-71E5-4C02-B1D3-240C1C4805EB"
        API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"  # 假設 API 端點

        params = {
            "Authorization": API_KEY,
            "locationName": city  # 目標城市
        }

        try:
            response = requests.get(API_URL, params=params, timeout=10)
            
            if response.status_code != 200:
                return f"無法獲取天氣資訊，錯誤碼: {response.status_code}"

            data = response.json()
            
            try:
                location_data = next(
                    loc for loc in data["records"]["location"] if loc["locationName"] == city
                )
                
                weather_elements = location_data["weatherElement"]
                weather_report = {}

                for element in weather_elements:
                    element_name = element["elementName"]
                    forecast_time = element["time"][0]  # 取最近的預報資料
                    value = forecast_time["parameter"]["parameterName"]
                    unit = forecast_time["parameter"].get("parameterUnit", "")
                    weather_report[element_name] = f"{value} {unit}".strip()

                return weather_report

            except (KeyError, StopIteration):
                return "無法找到該城市的天氣資訊"
                
        except requests.exceptions.RequestException as e:
            return f"連接天氣服務失敗: {str(e)}"
        
        
    def get_map(self, location: str, radius: int = 1000, type: Optional[str] = None, keyword: Optional[str] = None, min_rating: float = 4.0, price_level: Optional[int] = None, open_now: bool = True) -> List[Dict]:
        """搜尋約會場所和餐廳
        
        參數:
            location: 位置名稱或地址 (可使用自然語言，例如「台南魯肉飯」、「西門町附近的鞋店」)
            radius: 搜尋半徑（米）- 固定為1000米
            type: 場所類型，限定在 restaurant, cafe, bar, park 等特定類型
            keyword: 關鍵字搜尋
            min_rating: 最低評分（0-5）
            price_level: 價格等級（0-4，0=免費, 4=非常昂貴）
            open_now: 是否僅顯示營業中的場所
            
        返回:
            符合條件的場所列表，包含店家介紹和詳細資訊
        """
        # 使用Text Search API直接搜尋地點
        # 構建查詢字符串
        API_KEY = "AIzaSyAu3hR8Izb_qLRKkxvXMjRggXZmyJ5km88"
        BASE_URL = "https://maps.googleapis.com/maps/api/place"
        TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

        query = location
        if type:
            query += f" {type}"
        if keyword:
            query += f" {keyword}"
        
        # 設置請求頭和主體
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': API_KEY,
            'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.priceLevel,places.id,places.photos,places.types,places.editorialSummary,places.googleMapsUri,places.websiteUri'
        }
        
        payload = {
            "textQuery": query,
            "languageCode": "zh-TW"
        }
        
        # 如果open_now為True，添加相應參數
        if open_now:
            payload["openNow"] = True
        
        # 發送請求
        response = requests.post(TEXT_SEARCH_URL, headers=headers, data=json.dumps(payload))
        
        # 檢查響應狀態
        if response.status_code != 200:
            return [{"error": f"搜尋失敗: {response.status_code} - {response.text}"}]
        
        data = response.json()
        
        # 如果沒有找到結果
        if 'places' not in data or not data['places']:
            return [{"error": f"無法找到相關地點: {query}"}]
        
        # 處理結果
        results = []
        for place in data.get('places', []):
            # 評分過濾
            if 'rating' in place and place['rating'] < min_rating:
                continue
                
            # 價格過濾
            if price_level is not None and 'priceLevel' in place and place['priceLevel'] != price_level:
                continue
                
            # 從place.id中提取PLACE_ID
            place_id = place['id'].split('/')[-1] if 'id' in place else ""
            
            # 建立結構化資料
            place_info = {
                "name": place.get('displayName', {}).get('text', "未知名稱"),
                "address": place.get('formattedAddress', "未知地址"),
                "rating": place.get('rating', "無評分"),
                "total_ratings": place.get('userRatingCount', 0),
                "price_level": place.get('priceLevel', "未標示"),
                "place_id": place_id,
                "types": place.get('types', []),
            }
            
            # 添加店家介紹（如果有）
            if 'editorialSummary' in place and place['editorialSummary'].get('text'):
                place_info["description"] = place['editorialSummary']['text']
            else:
                place_info["description"] = "暫無店家介紹"    

            # 添加Google地圖連結（如果有）
            if 'googleMapsUri' in place:
                place_info["maps_url"] = place['googleMapsUri']
            
            # 添加店家網站連結（如果有）
            if 'websiteUri' in place:
                place_info["website"] = place['websiteUri']
            
            # 添加顧客評價（如果有）
            if 'reviews' in place and place['reviews']:
                place_info["reviews"] = []
                for review in place['reviews'][:3]:  # 只取前3則評價
                    review_info = {
                        "rating": review.get('rating', 0),
                        "text": review.get('text', {}).get('text', "無評價內容"),
                        "time": review.get('relativePublishTimeDescription', "未知時間"),
                        "author": review.get('authorAttribution', {}).get('displayName', "匿名用戶")
                    }
                    place_info["reviews"].append(review_info)
            
            # 添加地理位置信息（如果有）
            if 'location' in place:
                place_info["location"] = {
                    "lat": place['location']['latitude'],
                    "lng": place['location']['longitude']
                }
            
            # 添加照片URL（如果有）
            if 'photos' in place and place['photos']:
                photo_name = place['photos'][0]['name']
                photo_id = photo_name.split('/')[-1]
                place_info["photo"] = f"{BASE_URL}/photo?maxwidth=400&photo_reference={photo_id}&key={API_KEY}"
            
            results.append(place_info)
                
        return results
            
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
        if user_input == "生成我的戀愛測驗結果吧！":
            image_url = tools.get_quiz_result(user_id)
            db.set_user_curr_status(user_id, 'quizzing')
            return [
                TextMessage(text="這是你的戀愛測驗結果！"),
                ImageMessage(original_content_url=image_url, preview_image_url=image_url)
            ]
        response = agent.invoke(user_input)
        output = [TextMessage(text=response,)]
        if len(db.get_user_quiz_messages(user_id)) > 10:
            output[0].quick_reply = QuickReply(
                items=[
                    QuickReplyItem(
                        action=MessageAction(label="生成戀愛測驗結果", text="生成我的戀愛測驗結果吧！")
                    )
                ]
            )
        logger.info(f"response: {output}")
        return output
        
    elif status == 'processing':
        return [TextMessage(text="正在生成中，請稍等！")]