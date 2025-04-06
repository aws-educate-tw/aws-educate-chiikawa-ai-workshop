import os
import requests
from typing import Literal
from pydantic import BaseModel, Field
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class WeatherArgs(BaseModel):
    city: Literal[
        '臺北市', '新北市', '桃園市', '臺中市', '臺南市', '高雄市',
        '基隆市', '新竹市', '嘉義市', '新竹縣', '苗栗縣', 
        '彰化縣', '南投縣', '雲林縣', '嘉義縣', '屏東縣',
        '宜蘭縣', '花蓮縣', '臺東縣', '澎湖縣', '金門縣', '連江縣'
    ] = Field(description="台灣縣市名稱")

def get_weather(city: str) -> str:
    logger.info(f"Weather tool called.")
    API_KEY = os.getenv("WEATHER_API_KEY")
    API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"

    params = {
        "Authorization": API_KEY,
        "locationName": city
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
                forecast_time = element["time"][0]
                value = forecast_time["parameter"]["parameterName"]
                unit = forecast_time["parameter"].get("parameterUnit", "")
                weather_report[element_name] = f"{value} {unit}".strip()

            return weather_report

        except (KeyError, StopIteration):
            return "無法找到該城市的天氣資訊"
            
    except requests.exceptions.RequestException as e:
        return f"連接天氣服務失敗: {str(e)}"
