# 智能食谱推荐系统

#  Session   食谱推荐项目创意与设计
#  Continue  mimo -s ses_115221afbffeiGlp4jMa5qVFWZ

基于用户个人属性、当前状态和环境因素的个性化食谱推荐系统。

## 功能特点

- 用户注册登录和个人信息管理
- 基于天气、地域、心情等多维度推荐
- 内置20+食谱库 + 在线食谱搜索
- 个性化口味偏好设置
- 推荐反馈和历史记录
- 食谱详情展示（食材、步骤）
- 响应式前端界面

## 技术栈

- **后端**: Python + FastAPI + SQLAlchemy
- **前端**: Vue.js 3
- **数据库**: SQLite
- **天气API**: 和风天气
- **部署**: Docker / Docker Compose

## 快速开始

### 方式一：直接运行

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入和风天气API Key

# 3. 启动服务
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 方式二：Docker运行

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 2. 启动服务
docker-compose up -d
```

### 访问应用

- **前端页面**: http://localhost:8000/app
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

## 项目结构

```
recipe-recommender/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI入口
│   │   ├── config.py         # 配置
│   │   ├── database.py       # 数据库
│   │   ├── models/           # 数据模型
│   │   ├── routers/          # API路由
│   │   ├── services/         # 业务逻辑
│   │   └── utils/            # 工具函数
│   ├── data/
│   │   └── recipes.json      # 内置食谱数据
│   ├── tests/                # 测试文件
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html            # 主页面
│   ├── css/style.css         # 样式
│   └── js/app.js             # Vue.js应用
├── docker-compose.yml
├── .env.example
├── README.md
└── USAGE.md
```

## API接口

### 认证相关
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 用户相关
- `GET /api/users/profile` - 获取用户资料
- `PUT /api/users/profile` - 更新用户资料
- `POST /api/users/state` - 提交用户状态

### 食谱相关
- `GET /api/recipes/` - 获取食谱列表
- `GET /api/recipes/{id}` - 获取食谱详情
- `GET /api/recipes/search/by-ingredients` - 按食材搜索
- `GET /api/recipes/search/online` - 在线搜索

### 推荐相关
- `GET /api/recommend/today` - 获取今日推荐
- `POST /api/recommend/feedback` - 提交推荐反馈
- `GET /api/recommend/history` - 推荐历史

## 推荐算法

系统综合以下因素进行推荐：

1. **天气因素** (30%): 温度、湿度、天气状况
2. **用户偏好** (25%): 口味偏好、历史评分
3. **地域因素** (20%): 家乡口味、异地需求
4. **用户状态** (15%): 身体感受、心情、想吃什么
5. **食谱质量** (10%): 评分、难度

## 内置食谱

系统包含20+内置食谱，涵盖：
- 川菜：麻婆豆腐、宫保鸡丁、回锅肉、鱼香肉丝、麻辣香锅
- 粤菜：排骨莲藕汤、皮蛋瘦肉粥、清蒸鲈鱼、冬瓜排骨汤
- 鲁菜：糖醋里脊
- 本帮菜：红烧肉
- 家常菜：番茄蛋花汤、凉拌黄瓜、酸辣土豆丝、蒜蓉西兰花、西红柿炒鸡蛋、红烧茄子、小米粥、绿豆汤
- 西北菜：羊肉泡馍

## 运行测试

```bash
cd backend
pytest tests/ -v
```

## 配置说明

### 和风天气API

1. 访问 https://dev.qweather.com/ 注册账号
2. 创建应用获取API Key
3. 将Key填入 `.env` 文件的 `WEATHER_API_KEY`

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| WEATHER_API_KEY | 和风天气API Key | 空（使用模拟数据） |
| SECRET_KEY | JWT密钥 | 需要修改 |
| DATABASE_URL | 数据库连接字符串 | sqlite:///./recipe.db |

## License

MIT
