import requests
from typing import Optional, Dict
from ..config import get_settings

settings = get_settings()


async def get_location_by_ip(ip: str = None) -> Optional[Dict]:
    """
    根据IP获取位置信息
    使用多个IP定位服务，提高成功率
    """
    # 如果是本地IP，尝试获取真实IP
    if not ip or ip in ["127.0.0.1", "localhost", "::1", "127.0.0.1:0"]:
        ip = await _get_real_ip()
    
    # 如果仍然没有IP，返回默认位置
    if not ip or ip in ["127.0.0.1", "localhost", "::1"]:
        return {"city": "深圳", "region": "广东", "country": "CN"}
    
    # 尝试多个IP定位服务
    services = [
        _try_ip_api_com,      # ip-api.com 支持中文，最可靠
        _try_ipinfo_io,       # ipinfo.io 返回英文
    ]
    
    for service in services:
        try:
            result = await service(ip)
            if result and result.get("city"):
                return result
        except Exception:
            continue
    
    return None


async def _get_real_ip() -> str:
    """通过外部服务获取真实IP"""
    services = [
        "https://httpbin.org/ip",
        "https://api.ipify.org?format=json",
        "https://ipinfo.io/json",
    ]
    
    for url in services:
        try:
            resp = requests.get(url, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                # 不同服务返回格式不同
                ip = data.get("origin", "") or data.get("ip", "")
                if ip:
                    # 如果有多个IP，取第一个
                    return ip.split(",")[0].strip()
        except Exception:
            continue
    
    return ""


async def _try_ip_api_com(ip: str) -> Optional[Dict]:
    """使用 ip-api.com 定位（支持中文，免费）"""
    try:
        url = f"http://ip-api.com/json/{ip}?lang=zh-CN&fields=status,country,regionName,city,lat,lon"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "success":
                return {
                    "city": data.get("city", ""),
                    "region": data.get("regionName", ""),
                    "country": data.get("country", ""),
                    "lat": data.get("lat"),
                    "lon": data.get("lon")
                }
    except Exception:
        pass
    return None


async def _try_ipinfo_io(ip: str) -> Optional[Dict]:
    """使用 ipinfo.io 定位"""
    try:
        url = f"https://ipinfo.io/{ip}/json"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            city = data.get("city", "")
            # ipinfo.io 返回的是英文城市名，需要转换
            city_cn = _translate_city_name(city)
            return {
                "city": city_cn or city,
                "region": data.get("region", ""),
                "country": data.get("country", ""),
                "loc": data.get("loc", "")
            }
    except Exception:
        pass
    return None


def _translate_city_name(city_en: str) -> str:
    """将英文城市名翻译为中文"""
    city_mapping = {
        "Beijing": "北京",
        "Shanghai": "上海",
        "Guangzhou": "广州",
        "Shenzhen": "深圳",
        "Chengdu": "成都",
        "Chongqing": "重庆",
        "Hangzhou": "杭州",
        "Wuhan": "武汉",
        "Xi'an": "西安",
        "Xian": "西安",
        "Tianjin": "天津",
        "Suzhou": "苏州",
        "Nanjing": "南京",
        "Changsha": "长沙",
        "Zhengzhou": "郑州",
        "Dongguan": "东莞",
        "Qingdao": "青岛",
        "Kunming": "昆明",
        "Ningbo": "宁波",
        "Hefei": "合肥",
        "Dalian": "大连",
        "Fuzhou": "福州",
        "Xiamen": "厦门",
        "Harbin": "哈尔滨",
        "Jinan": "济南",
        "Wenzhou": "温州",
        "Nanning": "南宁",
        "Changchun": "长春",
        "Shijiazhuang": "石家庄",
        "Taiyuan": "太原",
        "Nanchang": "南昌",
        "Guiyang": "贵阳",
        "Lanzhou": "兰州",
        "Haikou": "海口",
        "Hohhot": "呼和浩特",
        "Yinchuan": "银川",
        "Xining": "西宁",
        "Lhasa": "拉萨",
        "Urumqi": "乌鲁木齐",
        "Hong Kong": "香港",
        "Macau": "澳门",
        "Taipei": "台北",
    }
    return city_mapping.get(city_en, "")


# 城市名到和风天气Location ID的映射
CITY_TO_LOCATION_ID = {
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280101",
    "深圳": "101280601",
    "成都": "101270101",
    "重庆": "101040100",
    "杭州": "101210101",
    "武汉": "101200101",
    "西安": "101110101",
    "天津": "101030100",
    "苏州": "101190401",
    "南京": "101190101",
    "长沙": "101250101",
    "郑州": "101180101",
    "东莞": "101281601",
    "青岛": "101120201",
    "昆明": "101290101",
    "宁波": "101210401",
    "合肥": "101220101",
    "大连": "101070201",
    "福州": "101230101",
    "厦门": "101230201",
    "哈尔滨": "101050101",
    "济南": "101120101",
    "温州": "101210701",
    "南宁": "101300101",
    "长春": "101060101",
    "石家庄": "101090101",
    "太原": "101100101",
    "南昌": "101240101",
    "贵阳": "101260101",
    "兰州": "101160101",
    "海口": "101310101",
    "呼和浩特": "101080101",
    "银川": "101170101",
    "西宁": "101150101",
    "拉萨": "101140101",
    "乌鲁木齐": "101130101",
}

# 城市名到经纬度的映射（用于Open-Meteo API）
CITY_TO_COORDS = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579),
    "成都": (30.5728, 104.0668),
    "重庆": (29.5630, 106.5516),
    "杭州": (30.2741, 120.1551),
    "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398),
    "天津": (39.3434, 117.3616),
    "南京": (32.0603, 118.7969),
    "长沙": (28.2282, 112.9388),
    "郑州": (34.7466, 113.6253),
    "哈尔滨": (45.8038, 126.5350),
    "昆明": (25.0389, 102.7183),
    "海口": (20.0440, 110.1999),
    "乌鲁木齐": (43.8256, 87.6168),
}


async def get_weather_by_city(city: str) -> Optional[Dict]:
    """根据城市名获取天气信息"""
    if not settings.WEATHER_API_KEY:
        return await _get_weather_from_open_meteo(city)

    try:
        # 获取Location ID
        location_id = CITY_TO_LOCATION_ID.get(city)
        
        if location_id:
            # 尝试使用和风天气API
            try:
                weather_url = "https://devapi.qweather.com/v7/weather/now"
                weather_params = {
                    "location": location_id,
                    "key": settings.WEATHER_API_KEY
                }

                weather_resp = requests.get(weather_url, params=weather_params, timeout=5)
                weather_data = weather_resp.json()

                if weather_data.get("code") == "200":
                    now = weather_data.get("now", {})
                    return {
                        "temp": float(now.get("temp", 0)),
                        "feels_like": float(now.get("feelsLike", 0)),
                        "humidity": float(now.get("humidity", 0)),
                        "condition": now.get("text", ""),
                        "wind_dir": now.get("windDir", ""),
                        "wind_speed": float(now.get("windSpeed", 0)),
                        "city": city
                    }
            except Exception:
                pass
        
        # 如果和风天气失败，使用Open-Meteo
        return await _get_weather_from_open_meteo(city)
        
    except Exception as e:
        print(f"天气API调用失败: {e}")
        return await _get_weather_from_open_meteo(city)


async def _get_weather_from_open_meteo(city: str) -> Optional[Dict]:
    """使用Open-Meteo API获取天气（免费，无需API key）"""
    try:
        # 获取城市坐标
        coords = CITY_TO_COORDS.get(city)
        if not coords:
            # 默认使用深圳坐标
            coords = (22.5431, 114.0579)
        
        lat, lon = coords
        
        # Open-Meteo API
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m,wind_direction_10m&timezone=Asia/Shanghai"
        
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            current = data.get("current", {})
            
            temp = current.get("temperature_2m", 0)
            humidity = current.get("relative_humidity_2m", 0)
            wind_speed = current.get("wind_speed_10m", 0)
            wind_dir = _get_wind_direction(current.get("wind_direction_10m", 0))
            weather_code = current.get("weather_code", 0)
            condition = _get_weather_condition(weather_code)
            
            return {
                "temp": temp,
                "feels_like": temp - 2,  # 简单估算
                "humidity": humidity,
                "condition": condition,
                "wind_dir": wind_dir,
                "wind_speed": wind_speed,
                "city": city
            }
    except Exception as e:
        print(f"Open-Meteo API调用失败: {e}")
    
    return _get_mock_weather(city)


def _get_wind_direction(degrees: float) -> str:
    """将风向角度转换为中文"""
    directions = ["北风", "东北风", "东风", "东南风", "南风", "西南风", "西风", "西北风"]
    index = round(degrees / 45) % 8
    return directions[index]


def _get_weather_condition(code: int) -> str:
    """将WMO天气代码转换为中文描述"""
    conditions = {
        0: "晴",
        1: "大部晴朗",
        2: "多云",
        3: "阴",
        45: "雾",
        48: "雾凇",
        51: "小毛毛雨",
        53: "中毛毛雨",
        55: "大毛毛雨",
        56: "冻毛毛雨",
        57: "强冻毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        66: "冻雨",
        67: "强冻雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "雪粒",
        80: "小阵雨",
        81: "中阵雨",
        82: "大阵雨",
        85: "小阵雪",
        86: "大阵雪",
        95: "雷暴",
        96: "雷暴伴小冰雹",
        99: "雷暴伴大冰雹",
    }
    return conditions.get(code, "未知")


def _get_mock_weather(city: str) -> Dict:
    """模拟天气数据（当API不可用时）"""
    import random
    
    # 根据城市返回更真实的模拟数据
    base_temps = {
        "北京": 5, "上海": 12, "广州": 22, "深圳": 25,
        "成都": 15, "重庆": 16, "杭州": 14, "武汉": 10,
        "西安": 8, "天津": 6, "南京": 13, "长沙": 11,
        "哈尔滨": -10, "昆明": 18, "海口": 28, "乌鲁木齐": -5,
    }
    
    base_temp = base_temps.get(city, 15)
    # 添加一些随机变化
    temp = base_temp + random.randint(-3, 3)
    humidity = random.randint(30, 80)
    
    conditions = ["晴", "多云", "阴", "小雨"]
    weights = [0.4, 0.3, 0.2, 0.1]
    condition = random.choices(conditions, weights=weights, k=1)[0]
    
    wind_dirs = ["北风", "南风", "东风", "西风", "东北风", "西南风"]
    
    return {
        "temp": temp,
        "feels_like": temp - 2,
        "humidity": humidity,
        "condition": condition,
        "wind_dir": random.choice(wind_dirs),
        "wind_speed": random.randint(3, 20),
        "city": city
    }


def analyze_weather_for_recipe(weather: Dict) -> Dict[str, float]:
    """分析天气条件，返回推荐权重调整因子"""
    factors = {
        "hot_soup": 0.0,
        "cold_dish": 0.0,
        "spicy": 0.0,
        "light": 0.0,
        "moistening": 0.0,
    }

    temp = weather.get("temp", 20)
    humidity = weather.get("humidity", 50)
    condition = weather.get("condition", "")

    if temp < 10:
        factors["hot_soup"] = 0.8
        factors["spicy"] = 0.3
    elif temp < 20:
        factors["hot_soup"] = 0.4
    elif temp > 30:
        factors["cold_dish"] = 0.7
        factors["light"] = 0.6

    if humidity < 40:
        factors["moistening"] = 0.7
    elif humidity > 75:
        factors["light"] = 0.4

    if "雨" in condition or "雪" in condition:
        factors["hot_soup"] = max(factors["hot_soup"], 0.6)

    return factors
