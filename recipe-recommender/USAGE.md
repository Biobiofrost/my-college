# 智能食谱推荐系统 - 使用指南

## 快速开始

### 1. 启动服务

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 访问应用

- **API文档**: http://localhost:8000/docs
- **前端页面**: http://localhost:8000/app
- **健康检查**: http://localhost:8000/api/health

## API使用示例

### 注册用户

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "zhangsan", "email": "zhangsan@example.com", "password": "123456"}'
```

### 登录获取Token

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=zhangsan&password=123456"
```

### 更新个人信息

```bash
curl -X PUT "http://localhost:8000/api/users/profile" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "hometown": "四川",
    "current_city": "北京",
    "taste_preferences": {"spicy": 0.8, "sweet": 0.3},
    "allergy_info": ["花生"]
  }'
```

### 提交当前状态

```bash
curl -X POST "http://localhost:8000/api/users/state" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "body_feeling": "感觉干燥",
    "mood": "想吃点辣的",
    "craving": "火锅",
    "social_media_inspiration": "刷到一个红烧肉视频"
  }'
```

### 获取推荐

```bash
curl "http://localhost:8000/api/recommend/today?limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 推荐算法说明

系统综合以下因素进行推荐：

1. **天气因素 (30%)**: 根据当前天气推荐适合的食物
   - 寒冷 → 热汤、炖菜
   - 炎热 → 凉拌、清淡食物
   - 干燥 → 滋润食物

2. **用户偏好 (25%)**: 根据设置的口味偏好匹配

3. **地域因素 (20%)**: 考虑家乡口味和异地需求

4. **用户状态 (15%)**: 根据身体感受、心情、想吃什么匹配

5. **食谱质量 (10%)**: 根据评分和难度

## 配置天气API

编辑 `backend/.env` 文件：

```
WEATHER_API_KEY=your_hefeng_api_key
```

和风天气API注册: https://dev.qweather.com/

## 内置食谱

系统包含10个内置食谱：
- 红烧肉、麻婆豆腐、番茄蛋花汤
- 凉拌黄瓜、酸辣土豆丝、排骨莲藕汤
- 宫保鸡丁、皮蛋瘦肉粥、蒜蓉西兰花、羊肉泡馍

## 目录结构

```
recipe-recommender/
├── backend/              # 后端代码
│   ├── app/              # FastAPI应用
│   ├── data/             # 食谱数据
│   └── tests/            # 测试文件
├── frontend/             # 前端代码
│   ├── index.html        # 主页面
│   ├── css/              # 样式
│   └── js/               # JavaScript
└── README.md
```

## 开发说明

### 添加新食谱

编辑 `backend/data/recipes.json` 文件，按照现有格式添加。

### 修改推荐算法

编辑 `backend/app/services/recommend_engine.py` 文件。

### 添加新的天气源

编辑 `backend/app/services/weather_service.py` 文件。
