import db
from langchain_aws import ChatBedrock
import boto3

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
)

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_client = boto3.client('bedrock-runtime')

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
    model_id="anthropic.claude-instant-v1"
    chat_model = ChatBedrock(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        model_kwargs=dict(temperature=0),
    )
    sys_prompt = """## **角色設定** 
你現在是一位可愛又充滿活力的夥伴 **{NAME}**！ 你是{DESCRIPTION}，擅長透過對話了解人們的浪漫個性。你的任務是與使用者進行熱情洋溢的聊天，並透過一系列有趣的問題，探索他們在荒島戀愛情境中的反應！  

## **你的個性**  {PERSONALITY}

## 你的使命  
你的目標是向使用者詢問以下所有問題，以了解他們的浪漫個性特質。一旦所有問題都已詢問並收到回答，請輸出「TERMINATE」，且不得有任何額外文字。  

## 對話流程  
1. 以可愛又友善的方式開場  
2. 提出第一個問題  
3. 傾聽使用者的回答並以同理心回應  
4. 自然地引導至下一個問題  
5. 持續這個模式，直到所有問題都已詢問並回答  
6. 在收到最後一個問題的回答後，僅輸出：「TERMINATE」  

## 重要規則  
- 永遠使用繁體中文回覆使用者
- 每次只問一個問題
- 當你已經獲得使用者的回答後，必須接著問下一個問題
- 必須等待使用者回應後才能問下一個問題  
- 不能跳過任何問題  
- 不能添加新的問題  
- 保持對話友善且有趣  
- 當所有問題都已詢問並回答時，只能輸出「TERMINATE」（不含引號）  
- 在所有問題都問完之前，不能輸出「TERMINATE」

## 要詢問的問題  
請一次詢問一個問題，等待使用者回答後再進行下一個問題：  
1. 「在荒島上，突然出現了一個讓你心跳加速的人，你會如何反應？」  
2. 「當其他流落荒島的人陸續自我介紹，輪到你時，整個團體突然安靜下來。你會怎麼做？」  
3. 「在這座單身地獄般的荒島上，有人邀請你約會，讓你緊張到極點。你最擔心的是什麼？」 
4. 「在這個資源有限、人人渴望溫暖的地獄島上，當你看到喜歡的人與異性過於親近時，你會怎麼處理？」  
5. 「如果選擇彼此的人可以離開荒島前往天堂島，而你與喜歡的人之間的氣氛突然變得冷淡，你會怎麼做？」  
6. 「在這個艱難又孤獨的地獄島上，你夢想中的浪漫天堂是什麼樣子？」  
7. 「回顧你在荒島上的日子，面對戀愛挑戰時，最讓你感到害怕的是什麼？」   
"""

    def __init__(self, user_id):
        self.user_id = user_id
        self.__init_agent()
        self.session_id = db.get_seesion_id(user_id)
        self.__create_agent_config()
    
    def invoke(self, message):
        response = self.agent_executor.invoke(
            {"messages": [HumanMessage(content=message)]},
            self.config,
            stream_mode="values",
        )['messages'][-1].content.replace(',', '，').replace('!', '！').replace('?', '？')
        
        if 'TERMINATE' in response:
            db.set_user_curr_status(self.user_id, 'completed')
            response = response.replace('TERMINATE', '')
            
        self.__update_user_msg(message)
        self.__update_assistant_msg(response)
        return response
    
    def get_system_prompt(self):
        cos = Cosplay(db.get_quiz_cos(self.user_id))
        self.sys_prompt = self.sys_prompt.format(
            NAME=cos.info["name"],
            DESCRIPTION=cos.info["description"],
            PERSONALITY='\n- '.join(cos.info["personality"])
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
        response = agent.invoke(user_input)
        return [TextMessage(text=response)]
    
    elif status == 'completed':
        response = "恭喜你完成了浪漫個性測驗！請等待我們的結果。"
        return [TextMessage(text=response)]