# EEG疾病检测全链路知识库（优化版）

> **版本**：v2.0 优化版
> **更新时间**：2026年6月
> **优化内容**：深度细化、准确化、补充代码示例

---

## 知识库架构

```
EEG疾病检测知识库/
├── 模型知识库.md           ← 模型架构、设计哲学
├── 数据处理知识库.md       ← 本文档（优化版）
├── 模型训练知识库.md       ← 训练技巧、优化器
├── 模型部署知识库.md       ← 推理优化、边缘部署
└── 工程化知识库.md         ← MLOps、监控告警
```

---

## 1. EEG数据特性深度解析

### 1.1 频域特性

| 频段 | 频率范围 | 脑区 | 功能 | 疾病关联 |
|------|----------|------|------|----------|
| **δ (Delta)** | 0.5-4Hz | 额叶 | 深度睡眠、昏迷 | 脑损伤、昏迷 |
| **θ (Theta)** | 4-8Hz | 颞叶 | 记忆、情绪 | 癫痫、ADHD |
| **α (Alpha)** | 8-13Hz | 枕叶 | 放松、闭眼 | 焦虑、抑郁 |
| **β (Beta)** | 13-30Hz | 额叶 | 专注、思考 | 焦虑、失眠 |
| **γ (Gamma)** | 30-100Hz | 全脑 | 认知、绑定 | 精神分裂 |

### 1.2 空间特性

**电极系统**：
- 10-20系统：19个标准电极
- 10-10系统：64个电极
- 10-5系统：128个电极
- 高密度：256个电极

**脑区划分**：
```
额叶(F): 执行功能、决策
颞叶(T): 听觉、记忆
顶叶(P): 体感、空间
枕叶(O): 视觉
中央(C): 运动
```

### 1.3 时序特性

**采样率**：
- 临床EEG：256Hz
- 研究级：512-1024Hz
- 高密度：2048Hz

**时间尺度**：
- 事件相关电位(ERP)：100-500ms
- 节律振荡：秒级
- 睡眠周期：分钟级
- 癫痫发作：秒-分钟级

---

## 2. 预处理流程深度解析

### 2.1 滤波详解

**带通滤波**：
```python
import mne

# 加载数据
raw = mne.io.read_raw_edf('eeg_data.edf', preload=True)

# 带通滤波：0.5-40Hz
raw.filter(l_freq=0.5, h_freq=40, method='fir', fir_design='firwin')

# 陷波滤波：50Hz（工频干扰）
raw.notch_filter(freqs=50, method='fir')
```

**滤波器选择**：
| 滤波器类型 | 特点 | 适用场景 |
|------------|------|----------|
| FIR | 线性相位、稳定 | 通用 |
| IIR | 计算高效 | 实时系统 |
| Butterworth | 平坦通带 | 通用 |
| Chebyshev | 陡峭过渡 | 需要锐截止 |

### 2.2 ICA去伪迹详解

**ICA流程**：
```python
from mne.preprocessing import ICA

# 创建ICA对象
ica = ICA(n_components=20, random_state=42, method='fastica')

# 拟合ICA
ica.fit(raw)

# 识别伪迹成分
# 眼电成分：高权重在额叶电极
# 肌电成分：高权重在颞叶电极

# 去除伪迹成分
ica.exclude = [0, 1]  # 假设成分0和1是伪迹
raw_clean = ica.apply(raw.copy())
```

**ICA成分识别**：
| 成分类型 | 空间分布 | 频谱特征 | 时间特征 |
|----------|----------|----------|----------|
| 眼电(EOG) | 额叶集中 | 低频主导 | 突发脉冲 |
| 肌电(EMG) | 颞叶集中 | 高频宽带 | 持续噪声 |
| 心电(ECG) | 全脑均匀 | 周期性峰 | 规则间隔 |

### 2.3 重参考详解

**参考方法**：
```python
# 平均参考
raw.set_eeg_reference('average')

# 拉普拉斯参考（局部平均）
raw.set_eeg_reference('REST')

# 自定义参考
raw.set_eeg_reference(ref_channels=['Cz'])
```

**参考方法对比**：
| 方法 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 平均参考 | 简单、常用 | 假设均匀分布 | 通用 |
| 拉普拉斯参考 | 局部聚焦 | 计算复杂 | 源定位 |
| REST参考 | 无偏估计 | 需要头模型 | 研究级 |

### 2.4 分段(Epoching)详解

**分段流程**：
```python
# 创建事件
events = mne.find_events(raw, stim_channel='STI 014')

# 定义事件ID
event_id = {'visual': 1, 'auditory': 2}

# 创建epochs
epochs = mne.Epochs(raw, events, event_id, 
                    tmin=-0.2, tmax=0.8, 
                    baseline=(-0.2, 0),
                    reject=dict(eeg=100e-6),  # 拒绝阈值
                    preload=True)
```

**参数设置**：
| 参数 | 推荐值 | 说明 |
|------|--------|------|
| tmin | -0.2s | 基线开始 |
| tmax | 0.8s | 任务结束 |
| baseline | (-0.2, 0) | 基线校正 |
| reject | 100μV | 拒绝坏段 |

---

## 3. 特征工程深度解析

### 3.1 时域特征

**统计特征**：
```python
import numpy as np

def extract_time_features(epoch):
    """提取时域特征"""
    features = {}
    
    # 基本统计
    features['mean'] = np.mean(epoch)
    features['std'] = np.std(epoch)
    features['var'] = np.var(epoch)
    features['skew'] = scipy.stats.skew(epoch)
    features['kurtosis'] = scipy.stats.kurtosis(epoch)
    
    # 峰值特征
    features['peak_to_peak'] = np.max(epoch) - np.min(epoch)
    features['rms'] = np.sqrt(np.mean(epoch**2))
    
    # 过零率
    zero_crossings = np.sum(np.diff(np.sign(epoch)) != 0)
    features['zero_crossing_rate'] = zero_crossings / len(epoch)
    
    return features
```

### 3.2 频域特征

**功率谱特征**：
```python
from scipy import signal

def extract_freq_features(epoch, sfreq=256):
    """提取频域特征"""
    features = {}
    
    # 计算功率谱密度
    freqs, psd = signal.welch(epoch, sfreq, nperseg=256)
    
    # 频带能量
    bands = {
        'delta': (0.5, 4),
        'theta': (4, 8),
        'alpha': (8, 13),
        'beta': (13, 30),
        'gamma': (30, 100)
    }
    
    for band_name, (fmin, fmax) in bands.items():
        mask = (freqs >= fmin) & (freqs <= fmax)
        features[f'{band_name}_power'] = np.mean(psd[mask])
    
    # 相对功率
    total_power = np.sum(psd)
    for band_name in bands.keys():
        features[f'{band_name}_relative'] = features[f'{band_name}_power'] / total_power
    
    # 频谱熵
    psd_norm = psd / np.sum(psd)
    features['spectral_entropy'] = -np.sum(psd_norm * np.log2(psd_norm + 1e-12))
    
    return features
```

### 3.3 时频特征

**小波变换**：
```python
import pywt

def extract_wavelet_features(epoch, wavelet='db4', level=5):
    """提取小波特征"""
    features = {}
    
    # 小波分解
    coeffs = pywt.wavedec(epoch, wavelet, level=level)
    
    # 各层能量
    for i, coeff in enumerate(coeffs):
        features[f'wavelet_energy_level_{i}'] = np.sum(coeff**2)
    
    # 各层熵
    for i, coeff in enumerate(coeffs):
        coeff_norm = coeff / np.sum(np.abs(coeff))
        features[f'wavelet_entropy_level_{i}'] = -np.sum(coeff_norm * np.log2(coeff_norm + 1e-12))
    
    return features
```

### 3.4 空间特征

**协方差矩阵**：
```python
def extract_spatial_features(epochs_data):
    """提取空间特征"""
    # epochs_data: (n_epochs, n_channels, n_times)
    features = {}
    
    # 计算协方差矩阵
    cov = np.cov(epochs_data.reshape(epochs_data.shape[0], -1))
    
    # 协方差矩阵特征
    features['cov_mean'] = np.mean(cov)
    features['cov_std'] = np.std(cov)
    
    # 特征值
    eigenvalues = np.linalg.eigvalsh(cov)
    features['eigenvalue_mean'] = np.mean(eigenvalues)
    features['eigenvalue_std'] = np.std(eigenvalues)
    
    return features
```

### 3.5 连接性特征

**功能连接性**：
```python
from mne_connectivity import spectral_connectivity_epochs

def extract_connectivity_features(epochs):
    """提取连接性特征"""
    # 计算相干性
    con = spectral_connectivity_epochs(epochs, method='coh', 
                                        fmin=8, fmax=13,  # Alpha频段
                                        mode='multitaper')
    
    # 连接性矩阵
    con_matrix = con.get_data()
    
    features = {}
    features['connectivity_mean'] = np.mean(con_matrix)
    features['connectivity_std'] = np.std(con_matrix)
    
    # 图论特征
    # 度中心性
    degree = np.sum(con_matrix > 0.5, axis=1)
    features['degree_mean'] = np.mean(degree)
    
    return features
```

---

## 4. 数据增强深度解析

### 4.1 时间域增强

```python
def time_shift(epoch, shift_max=0.2, sfreq=256):
    """时间平移"""
    shift_samples = int(shift_max * sfreq)
    shift = np.random.randint(-shift_samples, shift_samples)
    return np.roll(epoch, shift)

def time_stretch(epoch, rate_range=(0.8, 1.2)):
    """时间拉伸"""
    rate = np.random.uniform(*rate_range)
    indices = np.round(np.arange(0, len(epoch), rate)).astype(int)
    indices = indices[indices < len(epoch)]
    return epoch[indices]

def add_noise(epoch, noise_level=0.01):
    """添加高斯噪声"""
    noise = np.random.normal(0, noise_level, epoch.shape)
    return epoch + noise
```

### 4.2 频域增强

```python
def frequency_mask(epoch, sfreq=256, mask_ratio=0.1):
    """频域遮挡"""
    fft = np.fft.rfft(epoch)
    freqs = np.fft.rfftfreq(len(epoch), 1/sfreq)
    
    # 随机遮挡频段
    mask = np.random.random(len(fft)) > mask_ratio
    fft_masked = fft * mask
    
    return np.fft.irfft(fft_masked, len(epoch))
```

### 4.3 空间域增强

```python
def channel_dropout(epoch, dropout_ratio=0.1):
    """通道丢弃"""
    n_channels = epoch.shape[0]
    n_dropout = int(n_channels * dropout_ratio)
    dropout_idx = np.random.choice(n_channels, n_dropout, replace=False)
    
    epoch_aug = epoch.copy()
    epoch_aug[dropout_idx] = 0
    
    return epoch_aug

def channel_shuffle(epoch):
    """通道混洗"""
    perm = np.random.permutation(epoch.shape[0])
    return epoch[perm]
```

### 4.4 混合增强

```python
def mixup(epoch1, epoch2, alpha=0.2):
    """Mixup增强"""
    lam = np.random.beta(alpha, alpha)
    return lam * epoch1 + (1 - lam) * epoch2

def cutmix(epoch1, epoch2, alpha=0.2):
    """CutMix增强"""
    lam = np.random.beta(alpha, alpha)
    cut_len = int(len(epoch1) * (1 - lam))
    cut_start = np.random.randint(0, len(epoch1) - cut_len)
    
    epoch_aug = epoch1.copy()
    epoch_aug[cut_start:cut_start+cut_len] = epoch2[cut_start:cut_start+cut_len]
    
    return epoch_aug
```

---

## 5. 公开数据集详解

### 5.1 癫痫检测数据集

**CHB-MIT**：
- 规模：23例儿童患者
- 时长：983小时
- 采样率：256Hz
- 通道：23个
- 下载：physionet.org/chb-mit

**TUH EEG Corpus**：
- 规模：25,000+记录
- 时长：3,000+小时
- 标注：癫痫发作、背景
- 下载：isip.piconepress.com/projects/tuh_eeg

### 5.2 脑机接口数据集

**BCI Competition IV**：
- 数据集1：运动想象（4类）
- 数据集2a：运动想象（4类，9受试者）
- 数据集2b：运动想象（2类，9受试者）
- 下载：bbci.de/competition/iv

**PhysioNet MI**：
- 规模：109受试者
- 任务：运动想象（4类）
- 采样率：160Hz
- 下载：physionet.org/pn4/eegmmidb

### 5.3 情绪识别数据集

**SEED**：
- 规模：15受试者，15次实验
- 任务：情绪识别（3类）
- 采样率：200Hz
- 通道：62个
- 下载：bcmi.sjtu.edu.cn/home/seed

**DEAP**：
- 规模：32受试者
- 任务：情绪识别（4维）
- 采样率：128Hz
- 通道：32个
- 下载：www.eecs.qmul.ac.uk/mmv/datasets/deap

### 5.4 睡眠分期数据集

**Sleep-EDF**：
- 规模：197例健康受试者
- 时长：全夜睡眠
- 采样率：100Hz
- 标注：5个睡眠阶段
- 下载：physionet.org/pn6/sleep-edfx

**SHHS**：
- 规模：5,804例
- 时长：全夜睡眠
- 标注：5个睡眠阶段
- 下载：sleepdata.org

---

## 6. 工具箱深度对比

### 6.1 MNE-Python

**优势**：
- 功能全面：从预处理到源定位
- 社区活跃：持续更新
- 文档详细：教程丰富
- 集成度高：与sklearn、PyTorch集成

**代码示例**：
```python
import mne

# 完整预处理流程
raw = mne.io.read_raw_edf('data.edf', preload=True)
raw.filter(0.5, 40)
raw.notch_filter(50)

# ICA去伪迹
ica = mne.preprocessing.ICA(n_components=20)
ica.fit(raw)
ica.exclude = [0, 1]
raw = ica.apply(raw)

# 创建epochs
events = mne.find_events(raw)
epochs = mne.Epochs(raw, events, tmin=-0.2, tmax=0.8, baseline=(-0.2, 0))
```

### 6.2 EEGLAB

**优势**：
- GUI界面：操作直观
- 插件丰富：扩展性强
- 研究级：学术界标准
- MATLAB：性能好

**适用场景**：
- 传统EEG分析
- 需要GUI操作
- MATLAB环境

### 6.3 braindecode

**优势**：
- 深度学习专用
- PyTorch集成
- 模型丰富
- 端到端训练

**代码示例**：
```python
from braindecode import EEGClassifier
from braindecode.models import EEGNet

# 创建模型
model = EEGNet(n_chans=64, n_outputs=2, n_times=256)

# 训练
clf = EEGClassifier(model, max_epochs=100)
clf.fit(X_train, y_train)
```

---

## 7. 数据质量控制自动化

### 7.1 自动化检测

```python
def auto_quality_check(epochs, threshold=100e-6):
    """自动化质量检测"""
    quality = {}
    
    # 1. 振幅检测
    amplitude = np.max(np.abs(epochs.get_data()), axis=(1, 2))
    quality['amplitude_bad'] = np.where(amplitude > threshold)[0]
    
    # 2. 方差检测
    variance = np.var(epochs.get_data(), axis=(1, 2))
    quality['variance_bad'] = np.where(variance > np.median(variance) * 3)[0]
    
    # 3. 平坦度检测
    flatness = np.std(epochs.get_data(), axis=2)
    quality['flat_bad'] = np.where(np.min(flatness, axis=1) < 1e-7)[0]
    
    # 合并坏段
    quality['all_bad'] = np.unique(np.concatenate([
        quality['amplitude_bad'],
        quality['variance_bad'],
        quality['flat_bad']
    ]))
    
    return quality
```

### 7.2 可视化检查

```python
def plot_quality_report(epochs, quality):
    """可视化质量报告"""
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    # 振幅分布
    axes[0, 0].hist(np.max(np.abs(epochs.get_data()), axis=(1, 2)), bins=50)
    axes[0, 0].set_title('Amplitude Distribution')
    
    # 方差分布
    axes[0, 1].hist(np.var(epochs.get_data(), axis=(1, 2)), bins=50)
    axes[0, 1].set_title('Variance Distribution')
    
    # 坏段标记
    axes[1, 0].bar(['Good', 'Bad'], 
                   [len(epochs) - len(quality['all_bad']), len(quality['all_bad'])])
    axes[1, 0].set_title('Epoch Quality')
    
    # 通道质量
    channel_quality = np.std(epochs.get_data(), axis=(0, 2))
    axes[1, 1].bar(range(len(channel_quality)), channel_quality)
    axes[1, 1].set_title('Channel Quality')
    
    plt.tight_layout()
    plt.savefig('quality_report.png')
```

---

## 8. 多模态融合

### 8.1 EEG + 眼动

```python
def fuse_eeg_eyetracking(eeg_data, eyetracking_data):
    """EEG与眼动数据融合"""
    # 时间对齐
    eeg_times = np.arange(len(eeg_data)) / 256  # 256Hz
    et_times = np.arange(len(eyetracking_data)) / 60  # 60Hz
    
    # 插值对齐
    from scipy.interpolate import interp1d
    f = interp1d(et_times, eyetracking_data, kind='linear')
    eyetracking_aligned = f(eeg_times)
    
    # 特征融合
    fused = np.concatenate([eeg_data, eyetracking_aligned.reshape(-1, 1)], axis=1)
    
    return fused
```

### 8.2 EEG + fNIRS

```python
def fuse_eeg_fnirs(eeg_data, fnirs_data):
    """EEG与fNIRS数据融合"""
    # 不同时间尺度融合
    # EEG: 毫秒级
    # fNIRS: 秒级
    
    # 提取EEG特征（频域）
    eeg_features = extract_freq_features(eeg_data)
    
    # 提取fNIRS特征（HbO/HbR）
    fnirs_features = extract_fnirs_features(fnirs_data)
    
    # 特征级融合
    fused_features = {**eeg_features, **fnirs_features}
    
    return fused_features
```

---

## 9. 完整代码示例

### 9.1 端到端预处理

```python
import mne
import numpy as np
from mne.preprocessing import ICA

def preprocess_eeg(raw_path, l_freq=0.5, h_freq=40, notch_freq=50):
    """完整EEG预处理流程"""
    
    # 1. 加载数据
    raw = mne.io.read_raw_edf(raw_path, preload=True)
    
    # 2. 滤波
    raw.filter(l_freq, h_freq, method='fir', fir_design='firwin')
    raw.notch_filter(notch_freq, method='fir')
    
    # 3. ICA去伪迹
    ica = ICA(n_components=20, random_state=42, method='fastica')
    ica.fit(raw)
    
    # 自动识别眼电成分（假设额叶电极权重高）
    eog_indices, eog_scores = ica.find_bads_eog(raw, ch_name='Fp1')
    ica.exclude = eog_indices
    
    raw = ica.apply(raw)
    
    # 4. 重参考
    raw.set_eeg_reference('average')
    
    # 5. 创建epochs
    events = mne.find_events(raw, stim_channel='STI 014')
    epochs = mne.Epochs(raw, events, tmin=-0.2, tmax=0.8, 
                        baseline=(-0.2, 0), reject=dict(eeg=100e-6))
    
    return epochs

# 使用
epochs = preprocess_eeg('eeg_data.edf')
print(f"Good epochs: {len(epochs)}")
```

### 9.2 特征提取完整流程

```python
def extract_all_features(epochs):
    """提取所有特征"""
    features = {}
    
    # 时域特征
    features.update(extract_time_features(epochs.get_data()))
    
    # 频域特征
    features.update(extract_freq_features(epochs.get_data()))
    
    # 时频特征
    features.update(extract_wavelet_features(epochs.get_data()))
    
    # 空间特征
    features.update(extract_spatial_features(epochs.get_data()))
    
    return features
```

---

## 附录：学习资源

### 在线教程
- MNE-Python官方教程：mne.tools/dev/auto_tutorials
- braindecode教程：braindecode.org

### 书籍
- "EEG Signal Processing" - Saeid Sanei
- "Analyzing Neural Time Series Data" - Mike X Cohen

### 课程
- "Neural Data Science" - Coursera
- "Computational Neuroscience" - edX

---

> **📝 使用建议**：
> 1. 先理解EEG数据特性
> 2. 按照预处理流程实践
> 3. 尝试不同的特征提取方法
> 4. 使用公开数据集验证

---

*本知识库由AI辅助整理，供离线阅读和学习使用。*
