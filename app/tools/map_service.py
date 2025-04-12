import os
import requests
import json
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class MapArgs(BaseModel):
    location: str = Field(..., description="位置名稱或地址，可使用自然語言，例如「台南魯肉飯」、「西門町附近的鞋店」")
    radius: int = Field(1000, description="搜尋半徑（米）- 固定為1000米", ge=100, le=50000)
    type: Optional[str] = Field(None, description="場所類型，只能有以下幾種類別：restaurant, cafe, bar, park, movie_theater, amusement_park, art_gallery, museum, shopping_mall, tourist_attraction等")
    keyword: Optional[str] = Field(None, description="關鍵字搜尋")
    min_rating: float = Field(3.0, description="最低評分（0-5）", ge=0, le=5)
    price_level: Optional[Literal[0, 1, 2, 3, 4]] = Field(None, description="價格等級（0-4，0=免費, 4=非常昂貴）")
    open_now: bool = Field(True, description="是否僅顯示營業中的場所")

def get_map(location: str, radius: int = 1000, type: Optional[str] = None,
            keyword: Optional[str] = None, min_rating: float = 4.0,
            price_level: Optional[int] = None, open_now: bool = True) -> List[Dict]:
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
        logger.info(f"Map tool called.")

        API_KEY = os.getenv("MAP_API_KEY")
        BASE_URL = "https://maps.googleapis.com/maps/api/place"
        TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

        query = location
        if type:
            query += f" {type}"
        if keyword:
            query += f" {keyword}"
        
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': API_KEY,
            'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.priceLevel,places.id,places.photos,places.types,places.editorialSummary,places.googleMapsUri,places.websiteUri'
        }
        
        payload = {
            "textQuery": query,
            "languageCode": "zh-TW"
        }
        
        if open_now:
            payload["openNow"] = True
        
        response = requests.post(TEXT_SEARCH_URL, headers=headers, data=json.dumps(payload))
        
        if response.status_code != 200:
            return [{"error": f"搜尋失敗: {response.status_code} - {response.text}"}]
        
        data = response.json()
        
        # Error handling
        if 'places' not in data or not data['places']:
            return [{"error": f"無法找到相關地點: {query}"}]
        
        # Post-processing
        results = []
        for place in data.get('places', []):
            # Filter by rating & price
            if 'rating' in place and place['rating'] < min_rating:
                continue
                
            if price_level is not None and 'priceLevel' in place and place['priceLevel'] != price_level:
                continue
                
            # Extract PLACE_ID
            place_id = place['id'].split('/')[-1] if 'id' in place else ""
            
            place_info = {
                "name": place.get('displayName', {}).get('text', "未知名稱"),
                "address": place.get('formattedAddress', "未知地址"),
                "rating": place.get('rating', "無評分"),
                "total_ratings": place.get('userRatingCount', 0),
                "price_level": place.get('priceLevel', "未標示"),
                "place_id": place_id,
                "types": place.get('types', []),
            }
            
            # 添加店家介紹, Google地圖連結, 店家網站連結, 顧客評價, 地理位置信息, 照片URL
            if 'editorialSummary' in place and place['editorialSummary'].get('text'):
                place_info["description"] = place['editorialSummary']['text']
            else:
                place_info["description"] = "暫無店家介紹"    
            
            if 'reviews' in place and place['reviews']:
                place_info["reviews"] = []
                # Only get the first 3 reviews
                for review in place['reviews'][:3]:
                    review_info = {
                        "rating": review.get('rating', 0),
                        "text": review.get('text', {}).get('text', "無評價內容"),
                        "time": review.get('relativePublishTimeDescription', "未知時間"),
                        "author": review.get('authorAttribution', {}).get('displayName', "匿名用戶")
                    }
                    place_info["reviews"].append(review_info)
            
            results.append(place_info)
        print(f"Results: {results}")
        return results
