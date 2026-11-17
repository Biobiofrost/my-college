const { createApp, ref, computed, onMounted, watch } = Vue;

const API_BASE = '/api';

const app = createApp({
    setup() {
        const currentPage = ref('home');
        const isLoggedIn = ref(false);
        const isLoading = ref(false);
        const token = ref('');
        const user = ref(null);

        const isRegister = ref(false);
        const authForm = ref({ username: '', email: '', password: '' });
        const authError = ref('');

        const currentMealType = ref('');
        const weatherInfo = ref(null);
        const locationInfo = ref(null);
        const currentTime = ref('');
        const currentDate = ref('');
        const recommendMode = ref('normal');

        const guestForm = ref({
            city: '',
            body_feeling: '',
            craving: '',
            social_media_inspiration: ''
        });

        const stateForm = ref({
            body_feeling: '',
            mood: '',
            craving: '',
            social_media_inspiration: ''
        });

        const recommendations = ref([]);
        const recipes = ref([]);
        const searchKeyword = ref('');
        const selectedRecipe = ref(null);
        const recommendationHistory = ref([]);

        const profile = ref({
            hometown: '',
            current_city: '',
            taste_preferences: {
                spicy: 0.5,
                sweet: 0.5,
                sour: 0.5,
                salty: 0.5,
                light: 0.5,
                strong: 0.5
            },
            allergy_info: []
        });
        const allergyInput = ref('');
        const profileMessage = ref('');

        const regions = [
            '北京', '上海', '天津', '重庆',
            '河北', '山西', '辽宁', '吉林', '黑龙江',
            '江苏', '浙江', '安徽', '福建', '江西', '山东',
            '河南', '湖北', '湖南', '广东', '海南',
            '四川', '贵州', '云南', '陕西', '甘肃',
            '青海', '台湾', '广西', '西藏', '宁夏', '新疆',
            '内蒙古'
        ];

        const cities = [
            '北京', '上海', '广州', '深圳', '成都', '重庆', '杭州', '武汉',
            '西安', '天津', '苏州', '南京', '长沙', '郑州', '东莞', '青岛',
            '昆明', '宁波', '合肥', '大连', '福州', '厦门', '哈尔滨', '济南',
            '温州', '南宁', '长春', '石家庄', '太原', '南昌', '贵阳', '兰州',
            '海口', '呼和浩特', '银川', '西宁', '拉萨', '乌鲁木齐'
        ];

        const filterTags = ['川菜', '粤菜', '湘菜', '鲁菜', '本帮菜', '东北菜', '西北菜', '闽菜', '浙菜', '鄂菜', '滇菜', '桂菜', '家常菜'];
        const activeFilters = ref([]);

        const filteredRecipes = computed(() => {
            let result = recipes.value;
            if (activeFilters.value.length > 0) {
                result = result.filter(r => activeFilters.value.includes(r.cuisine));
            }
            if (searchKeyword.value) {
                const keyword = searchKeyword.value.toLowerCase();
                result = result.filter(r => 
                    r.name.toLowerCase().includes(keyword) ||
                    r.cuisine.toLowerCase().includes(keyword) ||
                    r.description?.toLowerCase().includes(keyword) ||
                    r.tags?.some(t => t.toLowerCase().includes(keyword))
                );
            }
            return result;
        });

        const getHeaders = () => {
            const headers = { 'Content-Type': 'application/json' };
            if (token.value) {
                headers['Authorization'] = `Bearer ${token.value}`;
            }
            return headers;
        };

        const loadMealType = async () => {
            try {
                const resp = await fetch(`${API_BASE}/recommend/meal-type`);
                if (resp.ok) {
                    const data = await resp.json();
                    currentMealType.value = data.meal_type;
                }
            } catch (e) {
                console.error('获取用餐类型失败', e);
            }
        };

        const updateTime = () => {
            const now = new Date();
            currentTime.value = now.toLocaleTimeString('zh-CN', { 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
            });
            currentDate.value = now.toLocaleDateString('zh-CN', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric',
                weekday: 'long'
            });
        };

        const loadLocationAndWeather = async () => {
            try {
                const resp = await fetch(`${API_BASE}/recommend/location`);
                if (resp.ok) {
                    const data = await resp.json();
                    locationInfo.value = {
                        city: data.city,
                        region: data.region,
                        ip: data.ip
                    };
                    if (data.weather) {
                        weatherInfo.value = data.weather;
                    }
                    if (data.meal_type) {
                        currentMealType.value = data.meal_type;
                    }
                }
            } catch (e) {
                console.error('获取位置和天气失败', e);
            }
        };

        const handleAuth = async () => {
            authError.value = '';
            try {
                if (isRegister.value) {
                    const resp = await fetch(`${API_BASE}/auth/register`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(authForm.value)
                    });
                    const data = await resp.json();
                    if (!resp.ok) throw new Error(data.detail || '注册失败');
                    isRegister.value = false;
                    authError.value = '注册成功，请登录';
                } else {
                    const formData = new URLSearchParams();
                    formData.append('username', authForm.value.username);
                    formData.append('password', authForm.value.password);

                    const resp = await fetch(`${API_BASE}/auth/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: formData
                    });
                    const data = await resp.json();
                    if (!resp.ok) throw new Error(data.detail || '登录失败');

                    token.value = data.access_token;
                    localStorage.setItem('token', token.value);
                    isLoggedIn.value = true;
                    await loadUser();
                    currentPage.value = 'home';
                }
            } catch (e) {
                authError.value = e.message;
            }
        };

        const loadUser = async () => {
            try {
                const resp = await fetch(`${API_BASE}/auth/me`, {
                    headers: getHeaders()
                });
                if (resp.ok) {
                    user.value = await resp.json();
                    profile.value = {
                        hometown: user.value.hometown || '',
                        current_city: user.value.current_city || '',
                        taste_preferences: user.value.taste_preferences || {
                            spicy: 0.5, sweet: 0.5, sour: 0.5, salty: 0.5, light: 0.5, strong: 0.5
                        },
                        allergy_info: user.value.allergy_info || []
                    };
                    allergyInput.value = (profile.value.allergy_info || []).join(',');
                    
                    // 如果用户有城市信息，更新天气
                    if (user.value.current_city) {
                        loadWeatherForCity(user.value.current_city);
                    }
                }
            } catch (e) {
                console.error('加载用户信息失败', e);
            }
        };

        const loadWeatherForCity = async (city) => {
            try {
                const resp = await fetch(`${API_BASE}/recommend/guest`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ city })
                });
                if (resp.ok) {
                    const data = await resp.json();
                    if (data.weather) {
                        weatherInfo.value = data.weather;
                    }
                }
            } catch (e) {
                console.error('获取天气失败', e);
            }
        };

        const logout = () => {
            token.value = '';
            localStorage.removeItem('token');
            isLoggedIn.value = false;
            user.value = null;
            currentPage.value = 'home';
            recommendations.value = [];
            recommendMode.value = 'normal';
        };

        const getGuestRecommend = async () => {
            isLoading.value = true;
            try {
                const resp = await fetch(`${API_BASE}/recommend/guest`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(guestForm.value)
                });
                if (resp.ok) {
                    const data = await resp.json();
                    recommendations.value = data;
                    recommendMode.value = data[0]?.mode || 'tourist';
                    
                    if (data.location) {
                        locationInfo.value = { city: data.location };
                    }
                    if (data.weather) {
                        weatherInfo.value = data.weather;
                    }
                }
            } catch (e) {
                console.error('获取推荐失败', e);
            } finally {
                isLoading.value = false;
            }
        };

        const submitState = async () => {
            isLoading.value = true;
            try {
                const resp = await fetch(`${API_BASE}/users/state`, {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify(stateForm.value)
                });
                if (resp.ok) {
                    await loadRecommendations();
                }
            } catch (e) {
                console.error('提交状态失败', e);
            } finally {
                isLoading.value = false;
            }
        };

        const loadRecommendations = async () => {
            try {
                const resp = await fetch(`${API_BASE}/recommend/today?limit=10`, {
                    headers: getHeaders()
                });
                if (resp.ok) {
                    const data = await resp.json();
                    recommendations.value = data;
                    recommendMode.value = data[0]?.mode || 'normal';
                }
            } catch (e) {
                console.error('加载推荐失败', e);
            }
        };

        const loadRecipes = async () => {
            try {
                const resp = await fetch(`${API_BASE}/recipes/`);
                if (resp.ok) {
                    recipes.value = await resp.json();
                }
            } catch (e) {
                console.error('加载食谱失败', e);
            }
        };

        const loadHistory = async () => {
            if (!isLoggedIn.value) return;
            try {
                const resp = await fetch(`${API_BASE}/recommend/history`, {
                    headers: getHeaders()
                });
                if (resp.ok) {
                    recommendationHistory.value = await resp.json();
                }
            } catch (e) {
                console.error('加载历史失败', e);
            }
        };

        const searchRecipes = async () => {
            // 前端过滤，不需要调用API
        };

        const toggleFilter = (tag) => {
            const index = activeFilters.value.indexOf(tag);
            if (index === -1) {
                activeFilters.value.push(tag);
            } else {
                activeFilters.value.splice(index, 1);
            }
        };

        const viewRecipe = async (id) => {
            try {
                const resp = await fetch(`${API_BASE}/recipes/${id}`);
                if (resp.ok) {
                    selectedRecipe.value = await resp.json();
                    currentPage.value = 'recipe-detail';
                }
            } catch (e) {
                console.error('获取食谱详情失败', e);
            }
        };

        const updateProfile = async () => {
            try {
                profile.value.allergy_info = allergyInput.value
                    .split(',')
                    .map(s => s.trim())
                    .filter(s => s);

                const resp = await fetch(`${API_BASE}/users/profile`, {
                    method: 'PUT',
                    headers: getHeaders(),
                    body: JSON.stringify(profile.value)
                });
                if (resp.ok) {
                    profileMessage.value = '保存成功';
                    await loadUser();
                    setTimeout(() => profileMessage.value = '', 3000);
                }
            } catch (e) {
                console.error('更新失败', e);
            }
        };

        const getRecipeColor = (cuisine) => {
            const colors = {
                '川菜': '#e74c3c',
                '粤菜': '#f39c12',
                '鲁菜': '#2ecc71',
                '本帮菜': '#9b59b6',
                '家常菜': '#3498db',
                '西北菜': '#e67e22',
                '湘菜': '#e74c3c',
                '东北菜': '#3498db',
                '浙菜': '#2ecc71',
                '闽菜': '#f39c12',
                '鄂菜': '#9b59b6',
                '滇菜': '#27ae60',
                '桂菜': '#e67e22',
                '津菜': '#3498db',
                '黔菜': '#8e44ad'
            };
            return colors[cuisine] || '#95a5a6';
        };

        const getRecipeEmoji = (tags) => {
            const emojiMap = {
                '辣': '🌶️',
                '汤': '🍲',
                '粥': '🥣',
                '凉拌': '🥗',
                '热菜': '🥘',
                '甜': '🍰',
                '清淡': '🥬',
                '家常': '🏠',
                '海鲜': '🦐',
                '面食': '🍜',
                '粉面': '🍜',
                '点心': '🥟',
                '早餐': '🌅',
                '小吃': '🍢',
                '荤菜': '🥩',
                '素菜': '🥬',
                '滋补': '💊'
            };
            if (tags) {
                for (const tag of tags) {
                    if (emojiMap[tag]) return emojiMap[tag];
                }
            }
            return '🍽️';
        };

        const getTasteLabel = (key) => {
            const labels = {
                spicy: '辣',
                sweet: '甜',
                sour: '酸',
                salty: '咸',
                light: '清淡',
                strong: '重口'
            };
            return labels[key] || key;
        };

        const formatDate = (dateStr) => {
            if (!dateStr) return '';
            const date = new Date(dateStr);
            return date.toLocaleDateString('zh-CN', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        };

        // 监听页面变化，加载历史记录
        watch(currentPage, (newPage) => {
            if (newPage === 'history') {
                loadHistory();
            }
        });

        onMounted(async () => {
            const savedToken = localStorage.getItem('token');
            if (savedToken) {
                token.value = savedToken;
                isLoggedIn.value = true;
                await loadUser();
            }
            
            // 更新时间
            updateTime();
            setInterval(updateTime, 1000);
            
            // 加载位置、天气和用餐类型
            await loadLocationAndWeather();
            
            // 加载食谱
            await loadRecipes();
        });

        return {
            currentPage,
            isLoggedIn,
            isLoading,
            isRegister,
            authForm,
            authError,
            currentMealType,
            weatherInfo,
            locationInfo,
            currentTime,
            currentDate,
            recommendMode,
            guestForm,
            stateForm,
            recommendations,
            recipes,
            searchKeyword,
            selectedRecipe,
            recommendationHistory,
            profile,
            allergyInput,
            profileMessage,
            regions,
            cities,
            filterTags,
            activeFilters,
            filteredRecipes,
            handleAuth,
            logout,
            getGuestRecommend,
            submitState,
            searchRecipes,
            toggleFilter,
            viewRecipe,
            updateProfile,
            getRecipeColor,
            getRecipeEmoji,
            getTasteLabel,
            formatDate
        };
    }
});

app.mount('#app');
