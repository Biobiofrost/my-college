# 分布式计算+EEG模型训练知识库

> **适用场景**：数据科学与大数据技术专业、PySpark分布式计算
> **更新时间**：2026年6月
> **定位**：将EEG理论转化为分布式实践

---

## 目录

1. [分布式计算基础](#1-分布式计算基础)
2. [PySpark核心概念](#2-pyspark核心概念)
3. [EEG数据分布式处理](#3-eeg数据分布式处理)
4. [分布式模型训练](#4-分布式模型训练)
5. [性能优化](#5-性能优化)
6. [实际案例](#6-实际案例)
7. [与MLOps集成](#7-与mlops集成)

---

## 1. 分布式计算基础

### 1.1 为什么需要分布式计算

**EEG数据规模**：
| 数据类型 | 单文件大小 | 数量 | 总规模 |
|----------|------------|------|--------|
| 单通道EEG | 10MB/小时 | 1000例 | 10GB |
| 多通道EEG | 100MB/小时 | 1000例 | 100GB |
| 高密度EEG | 1GB/小时 | 100例 | 100GB |
| 长程监测 | 10GB/天 | 100例 | 1TB |

**分布式计算优势**：
| 场景 | 单机 | 分布式 | 提升 |
|------|------|--------|------|
| 数据加载 | 10分钟 | 1分钟 | 10x |
| 特征提取 | 1小时 | 10分钟 | 6x |
| 模型训练 | 10小时 | 1小时 | 10x |
| 超参调优 | 100小时 | 10小时 | 10x |

### 1.2 分布式计算框架对比

| 框架 | 语言 | 特点 | 适用场景 |
|------|------|------|----------|
| **PySpark** | Python | 大数据处理 | 数据ETL、特征工程 |
| **Dask** | Python | 灵活、兼容 | 科学计算 |
| **Ray** | Python | 分布式ML | 模型训练、调优 |
| **Horovod** | Python | 分布式深度学习 | 大规模训练 |
| **PyTorch DDP** | Python | 原生分布式 | 深度学习 |

**PySpark优势**：
- 生态成熟：Hadoop、Spark生态
- 容错性强：自动故障恢复
- 扩展性好：线性扩展
- SQL支持：易用性高

---

## 2. PySpark核心概念

### 2.1 Spark架构

**核心组件**：
```
Spark应用
├── Driver（驱动程序）
│   ├── SparkContext
│   └── 用户代码
├── Cluster Manager（集群管理器）
│   ├── Standalone
│   ├── YARN
│   └── Kubernetes
└── Executors（执行器）
    ├── Task 1
    ├── Task 2
    └── Task N
```

**RDD vs DataFrame vs Dataset**：
| 类型 | 特点 | 适用场景 |
|------|------|----------|
| RDD | 低级API、灵活 | 复杂变换 |
| DataFrame | 高级API、优化 | 结构化数据 |
| Dataset | 类型安全 | Scala/Java |

### 2.2 PySpark基础操作

**初始化Spark**：
```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *

# 创建SparkSession
spark = SparkSession.builder \
    .appName("EEG Processing") \
    .config("spark.driver.memory", "8g") \
    .config("spark.executor.memory", "8g") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

# 设置日志级别
spark.sparkContext.setLogLevel("WARN")
```

**DataFrame操作**：
```python
# 读取数据
df = spark.read.parquet("hdfs://path/to/eeg/data")

# 基本操作
df.show(5)
df.printSchema()
df.describe().show()

# 过滤
filtered_df = df.filter(F.col("age") > 18)

# 选择
selected_df = df.select("patient_id", "eeg_data", "label")

# 聚合
agg_df = df.groupBy("label").agg(
    F.mean("eeg_power").alias("mean_power"),
    F.stddev("eeg_power").alias("std_power")
)
```

### 2.3 性能调优配置

**关键配置**：
```python
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")

# 内存配置
spark.conf.set("spark.driver.memory", "16g")
spark.conf.set("spark.executor.memory", "16g")
spark.conf.set("spark.executor.cores", "4")
spark.conf.set("spark.executor.instances", "10")

# 序列化
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
```

---

## 3. EEG数据分布式处理

### 3.1 数据格式转换

**EDF到Parquet**：
```python
import mne
import numpy as np
from pyspark.sql import Row

def edf_to_parquet(edf_path, output_path):
    """将EDF文件转换为Parquet格式"""
    
    # 读取EDF
    raw = mne.io.read_raw_edf(edf_path, preload=True)
    data = raw.get_data()
    
    # 转换为Spark DataFrame
    rows = []
    for i in range(data.shape[1]):
        row = Row(
            patient_id=edf_path.split('/')[-1].replace('.edf', ''),
            channel=i,
            data=data[:, i].tolist(),
            sfreq=raw.info['sfreq'],
            ch_names=raw.ch_names[i]
        )
        rows.append(row)
    
    df = spark.createDataFrame(rows)
    df.write.parquet(output_path)

# 批量转换
edf_files = ["file1.edf", "file2.edf", ...]
for edf_file in edf_files:
    edf_to_parquet(edf_file, f"hdfs://output/{edf_file}.parquet")
```

**批量处理**：
```python
def batch_process_edf(input_dir, output_dir):
    """批量处理EDF文件"""
    
    # 获取所有EDF文件
    import glob
    edf_files = glob.glob(f"{input_dir}/*.edf")
    
    # 并行处理
    spark.sparkContext.parallelize(edf_files) \
        .map(lambda f: edf_to_parquet(f, f"{output_dir}/{f.split('/')[-1]}.parquet")) \
        .collect()
```

### 3.2 特征提取分布式实现

**分布式特征提取**：
```python
from pyspark.sql import functions as F
from pyspark.sql.types import ArrayType, FloatType
import numpy as np

# 定义UDF（用户定义函数）
@F.udf(ArrayType(FloatType()))
def extract_power_spectrum(data, sfreq=256):
    """提取功率谱特征"""
    from scipy import signal
    
    freqs, psd = signal.welch(data, sfreq, nperseg=256)
    
    # 频带能量
    bands = {
        'delta': (0.5, 4),
        'theta': (4, 8),
        'alpha': (8, 13),
        'beta': (13, 30)
    }
    
    features = []
    for band_name, (fmin, fmax) in bands.items():
        mask = (freqs >= fmin) & (freqs <= fmax)
        features.append(float(np.mean(psd[mask])))
    
    return features

# 应用UDF
df_with_features = df.withColumn(
    "power_features",
    extract_power_spectrum(F.col("data"))
)
```

**分布式ICA**：
```python
def distributed_ica(df, n_components=20):
    """分布式ICA处理"""
    
    # 收集数据到Driver（小数据集）
    data = df.select("data").collect()
    data_array = np.array([row['data'] for row in data])
    
    # ICA处理
    from sklearn.decomposition import FastICA
    ica = FastICA(n_components=n_components)
    sources = ica.fit_transform(data_array)
    
    # 返回结果
    return sources
```

### 3.3 数据增强分布式实现

**分布式数据增强**：
```python
@F.udf(ArrayType(FloatType()))
def augment_eeg(data, augmentation_type="noise"):
    """分布式数据增强"""
    data = np.array(data)
    
    if augmentation_type == "noise":
        # 添加高斯噪声
        noise = np.random.normal(0, 0.01, data.shape)
        augmented = data + noise
    elif augmentation_type == "shift":
        # 时间平移
        shift = np.random.randint(-50, 50)
        augmented = np.roll(data, shift)
    elif augmentation_type == "scale":
        # 幅度缩放
        scale = np.random.uniform(0.8, 1.2)
        augmented = data * scale
    
    return augmented.tolist()

# 应用增强
df_augmented = df.withColumn(
    "augmented_data",
    augment_eeg(F.col("data"), F.lit("noise"))
)
```

---

## 4. 分布式模型训练

### 4.1 PySpark MLlib

**分布式机器学习**：
```python
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier, GBTClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

# 特征工程
assembler = VectorAssembler(
    inputCols=["delta_power", "theta_power", "alpha_power", "beta_power"],
    outputCol="features_raw"
)

scaler = StandardScaler(
    inputCol="features_raw",
    outputCol="features"
)

# 模型
rf = RandomForestClassifier(
    labelCol="label",
    featuresCol="features",
    numTrees=100,
    maxDepth=10
)

# Pipeline
pipeline = Pipeline(stages=[assembler, scaler, rf])

# 训练
model = pipeline.fit(train_df)

# 预测
predictions = model.transform(test_df)

# 评估
evaluator = MulticlassClassificationEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="accuracy"
)
accuracy = evaluator.evaluate(predictions)
print(f"Accuracy: {accuracy}")
```

**超参数调优**：
```python
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

# 参数网格
paramGrid = ParamGridBuilder() \
    .addGrid(rf.numTrees, [50, 100, 200]) \
    .addGrid(rf.maxDepth, [5, 10, 15]) \
    .build()

# 交叉验证
cv = CrossValidator(
    estimator=pipeline,
    estimatorParamMaps=paramGrid,
    evaluator=evaluator,
    numFolds=5,
    parallelism=4  # 并行度
)

# 训练
cv_model = cv.fit(train_df)
```

### 4.2 分布式深度学习

**PyTorch分布式训练**：
```python
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data.distributed import DistributedSampler

def setup(rank, world_size):
    """初始化分布式环境"""
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '12355'
    dist.init_process_group("nccl", rank=rank, world_size=world_size)

def train_ddp(rank, world_size, model, train_dataset):
    """分布式训练"""
    setup(rank, world_size)
    
    # 数据加载器
    train_sampler = DistributedSampler(train_dataset, num_replicas=world_size, rank=rank)
    train_loader = DataLoader(train_dataset, batch_size=32, sampler=train_sampler)
    
    # 模型
    model = model.to(rank)
    model = DDP(model, device_ids=[rank])
    
    # 优化器
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    
    # 训练循环
    for epoch in range(100):
        model.train()
        for batch in train_loader:
            data, target = batch
            data, target = data.to(rank), target.to(rank)
            
            optimizer.zero_grad()
            output = model(data)
            loss = torch.nn.functional.cross_entropy(output, target)
            loss.backward()
            optimizer.step()

# 启动分布式训练
import torch.multiprocessing as mp
mp.spawn(train_ddp, args=(world_size, model, train_dataset), nprocs=world_size)
```

**Horovod分布式训练**：
```python
import horovod.torch as hvd

# 初始化Horovod
hvd.init()

# 绑定GPU
torch.cuda.set_device(hvd.local_rank())

# 模型
model = EEGNet(n_channels=64, n_classes=2)
model.cuda()

# 优化器
optimizer = torch.optim.Adam(model.parameters(), lr=0.001 * hvd.size())

# 广播初始参数
hvd.broadcast_parameters(model.state_dict(), root_rank=0)
hvd.broadcast_optimizer_state(optimizer, root_rank=0)

# 包装优化器
optimizer = hvd.DistributedOptimizer(optimizer, named_parameters=model.named_parameters())

# 训练
for epoch in range(100):
    for batch in train_loader:
        optimizer.zero_grad()
        output = model(batch['data'].cuda())
        loss = torch.nn.functional.cross_entropy(output, batch['label'].cuda())
        loss.backward()
        optimizer.step()
```

### 4.3 Ray分布式调优

**Ray Tune超参数调优**：
```python
from ray import tune
from ray.tune.schedulers import ASHAScheduler
from ray.tune import CLIReporter

def train_eeg_model(config):
    """训练函数"""
    # 模型
    model = EEGNet(
        n_channels=config["n_channels"],
        n_classes=config["n_classes"],
        dropout=config["dropout"]
    )
    
    # 优化器
    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"])
    
    # 训练
    for epoch in range(config["epochs"]):
        # 训练代码
        train_loss = train_one_epoch(model, train_loader, optimizer)
        
        # 验证
        val_loss, val_acc = validate(model, val_loader)
        
        # 报告指标
        tune.report(loss=val_loss, accuracy=val_acc)

# 配置搜索空间
config = {
    "lr": tune.loguniform(1e-4, 1e-2),
    "dropout": tune.uniform(0.1, 0.5),
    "n_channels": 64,
    "n_classes": 2,
    "epochs": 100
}

# 调度器
scheduler = ASHAScheduler(
    metric="accuracy",
    mode="max",
    max_t=100,
    grace_period=10
)

# 报告器
reporter = CLIReporter(
    metric_columns=["loss", "accuracy", "training_iteration"]
)

# 运行调优
analysis = tune.run(
    train_eeg_model,
    config=config,
    num_samples=10,
    scheduler=scheduler,
    progress_reporter=reporter,
    resources_per_trial={"cpu": 2, "gpu": 1}
)

# 获取最佳参数
best_config = analysis.get_best_config(metric="accuracy", mode="max")
print(f"Best config: {best_config}")
```

---

## 5. 性能优化

### 5.1 数据分区优化

**分区策略**：
```python
# 按患者ID分区
df_partitioned = df.repartition("patient_id")

# 按数据大小分区
df_partitioned = df.repartition(100)

# 按列值分区
df_partitioned = df.repartitionByRange("label")

# 查看分区数
print(f"Partitions: {df_partitioned.rdd.getNumPartitions()}")
```

**分区最佳实践**：
| 策略 | 场景 | 效果 |
|------|------|------|
| 按患者ID | 患者级别处理 | 减少shuffle |
| 按数据大小 | 均匀分布 | 避免数据倾斜 |
| 按时间 | 时间序列处理 | 顺序处理 |

### 5.2 缓存策略

**缓存使用**：
```python
# 缓存DataFrame
df.cache()

# 持久化到磁盘
from pyspark import StorageLevel
df.persist(StorageLevel.MEMORY_AND_DISK)

# 取消缓存
df.unpersist()

# 查看缓存状态
print(spark.catalog.isCached("eeg_table"))
```

**缓存策略**：
| 策略 | 场景 | 效果 |
|------|------|------|
| MEMORY_ONLY | 小数据集 | 最快 |
| MEMORY_AND_DISK | 中等数据集 | 平衡 |
| DISK_ONLY | 大数据集 | 持久化 |

### 5.3 广播变量

**广播变量使用**：
```python
# 创建广播变量
lookup_table = {"class_1": 0, "class_2": 1}
broadcast_lookup = spark.sparkContext.broadcast(lookup_table)

# 使用广播变量
@F.udf(IntegerType())
def map_label(label):
    return broadcast_lookup.value.get(label, -1)

df_mapped = df.withColumn("label_id", map_label(F.col("label")))

# 释放广播变量
broadcast_lookup.destroy()
```

### 5.4 累加器

**累加器使用**：
```python
# 创建累加器
error_count = spark.sparkContext.accumulator(0)

def process_row(row):
    """处理每一行"""
    global error_count
    try:
        # 处理逻辑
        return process(row)
    except Exception:
        error_count.add(1)
        return None

# 应用
df_processed = df.rdd.map(process_row).collect()

print(f"Error count: {error_count.value}")
```

---

## 6. 实际案例

### 6.1 大规模EEG预处理

**完整流程**：
```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
import mne
import numpy as np

# 初始化Spark
spark = SparkSession.builder \
    .appName("EEG Preprocessing") \
    .config("spark.driver.memory", "16g") \
    .config("spark.executor.memory", "16g") \
    .config("spark.executor.cores", "4") \
    .config("spark.executor.instances", "10") \
    .getOrCreate()

# 1. 读取数据
df = spark.read.parquet("hdfs://data/eeg/raw")

# 2. 定义预处理UDF
@F.udf(ArrayType(FloatType()))
def preprocess_eeg(data, sfreq=256):
    """EEG预处理"""
    from scipy import signal
    
    data = np.array(data)
    
    # 带通滤波
    b, a = signal.butter(4, [0.5, 40], btype='band', fs=sfreq)
    data_filtered = signal.filtfilt(b, a, data)
    
    # 陷波滤波
    b, a = signal.iirnotch(50, 30, sfreq)
    data_filtered = signal.filtfilt(b, a, data_filtered)
    
    return data_filtered.tolist()

# 3. 应用预处理
df_preprocessed = df.withColumn(
    "data_processed",
    preprocess_eeg(F.col("data"), F.col("sfreq"))
)

# 4. 提取特征
@F.udf(ArrayType(FloatType()))
def extract_features(data, sfreq=256):
    """提取特征"""
    from scipy import signal
    
    data = np.array(data)
    freqs, psd = signal.welch(data, sfreq, nperseg=256)
    
    # 频带能量
    bands = {'delta': (0.5, 4), 'theta': (4, 8), 'alpha': (8, 13), 'beta': (13, 30)}
    features = []
    for (fmin, fmax) in bands.values():
        mask = (freqs >= fmin) & (freqs <= fmax)
        features.append(float(np.mean(psd[mask])))
    
    return features

df_features = df_preprocessed.withColumn(
    "features",
    extract_features(F.col("data_processed"), F.col("sfreq"))
)

# 5. 保存结果
df_features.write.parquet("hdfs://data/eeg/features")

# 6. 停止Spark
spark.stop()
```

### 6.2 分布式模型训练

**完整训练流程**：
```python
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import GBTClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

# 1. 加载数据
df = spark.read.parquet("hdfs://data/eeg/features")

# 2. 划分数据集
train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)

# 3. 特征工程
assembler = VectorAssembler(
    inputCols=["delta_power", "theta_power", "alpha_power", "beta_power"],
    outputCol="features_raw"
)

scaler = StandardScaler(
    inputCol="features_raw",
    outputCol="features"
)

# 4. 模型
gbt = GBTClassifier(
    labelCol="label",
    featuresCol="features",
    maxIter=100,
    maxDepth=10
)

# 5. Pipeline
pipeline = Pipeline(stages=[assembler, scaler, gbt])

# 6. 超参数调优
paramGrid = ParamGridBuilder() \
    .addGrid(gbt.maxIter, [50, 100, 200]) \
    .addGrid(gbt.maxDepth, [5, 10, 15]) \
    .build()

evaluator = MulticlassClassificationEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="accuracy"
)

cv = CrossValidator(
    estimator=pipeline,
    estimatorParamMaps=paramGrid,
    evaluator=evaluator,
    numFolds=5,
    parallelism=4
)

# 7. 训练
cv_model = cv.fit(train_df)

# 8. 评估
predictions = cv_model.transform(test_df)
accuracy = evaluator.evaluate(predictions)
print(f"Accuracy: {accuracy}")

# 9. 保存模型
cv_model.bestModel.write().overwrite().save("hdfs://models/eeg_model")
```

### 6.3 实时流处理

**Spark Streaming处理**：
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

# 初始化
spark = SparkSession.builder \
    .appName("EEG Streaming") \
    .getOrCreate()

# 读取流数据
stream_df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "eeg-data") \
    .load()

# 解析数据
schema = StructType([
    StructField("patient_id", StringType()),
    StructField("timestamp", TimestampType()),
    StructField("data", ArrayType(FloatType()))
])

parsed_df = stream_df \
    .select(from_json(col("value").cast("string"), schema).alias("data")) \
    .select("data.*")

# 实时处理
processed_df = parsed_df \
    .withColumn("features", extract_features(col("data"))) \
    .withColumn("prediction", predict_disease(col("features")))

# 写入输出
query = processed_df \
    .writeStream \
    .outputMode("append") \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("topic", "eeg-predictions") \
    .start()

query.awaitTermination()
```

---

## 7. 与MLOps集成

### 7.1 MLflow集成

**实验追踪**：
```python
import mlflow
import mlflow.spark

# 设置MLflow
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("eeg-classification")

# 训练并记录
with mlflow.start_run():
    # 记录参数
    mlflow.log_param("model_type", "GBT")
    mlflow.log_param("max_depth", 10)
    mlflow.log_param("max_iter", 100)
    
    # 训练模型
    model = pipeline.fit(train_df)
    
    # 记录指标
    predictions = model.transform(test_df)
    accuracy = evaluator.evaluate(predictions)
    mlflow.log_metric("accuracy", accuracy)
    
    # 记录模型
    mlflow.spark.log_model(model, "model")
    
    # 记录数据
    mlflow.log_artifact("hdfs://data/eeg/features")
```

### 7.2 DVC数据版本控制

**DVC使用**：
```bash
# 初始化DVC
dvc init

# 添加数据
dvc add data/eeg/raw

# 推送到远程存储
dvc push

# 拉取数据
dvc pull

# 查看数据版本
dvc dag
```

### 7.3 Kubernetes部署

**Spark on Kubernetes**：
```yaml
# spark-app.yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: eeg-processing
spec:
  type: Python
  mode: cluster
  image: spark:3.4.0
  mainApplicationFile: local:///opt/spark/work-dir/eeg_processing.py
  sparkVersion: "3.4.0"
  restartPolicy:
    type: OnFailure
    onFailureRetries: 3
  driver:
    cores: 2
    memory: "8g"
  executor:
    cores: 4
    memory: "16g"
    instances: 10
  deps:
    jars:
      - local:///opt/spark/jars/spark-sql-kafka-0-10_2.12-3.4.0.jar
```

### 7.4 Airflow工作流

**Airflow DAG**：
```python
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'eeg_processing_pipeline',
    default_args=default_args,
    description='EEG Processing Pipeline',
    schedule_interval=timedelta(days=1),
)

# 任务1：数据预处理
preprocess = SparkSubmitOperator(
    task_id='preprocess',
    application='/opt/spark/jobs/preprocess.py',
    conn_id='spark_default',
    dag=dag,
)

# 任务2：特征提取
extract_features = SparkSubmitOperator(
    task_id='extract_features',
    application='/opt/spark/jobs/extract_features.py',
    conn_id='spark_default',
    dag=dag,
)

# 任务3：模型训练
train_model = SparkSubmitOperator(
    task_id='train_model',
    application='/opt/spark/jobs/train_model.py',
    conn_id='spark_default',
    dag=dag,
)

# 任务依赖
preprocess >> extract_features >> train_model
```

---

## 附录：PySpark速查表

### 常用操作

```python
# 读取数据
df = spark.read.parquet("path")
df = spark.read.csv("path", header=True)
df = spark.read.json("path")

# 写入数据
df.write.parquet("path")
df.write.csv("path", header=True)
df.write.json("path")

# DataFrame操作
df.select("col1", "col2")
df.filter(col("col1") > 10)
df.groupBy("col1").agg(mean("col2"))
df.join(df2, "key")

# UDF
@udf(returnType=StringType())
def my_udf(x):
    return x.upper()

# 缓存
df.cache()
df.persist(StorageLevel.MEMORY_AND_DISK)
df.unpersist()
```

### 性能调优

```python
# 分区
df.repartition(100)
df.coalesce(50)

# 广播
broadcast_df = F.broadcast(df)

# 累加器
acc = spark.sparkContext.accumulator(0)
```

---

> **📝 使用建议**：
> 1. 先掌握PySpark基础
> 2. 理解EEG数据特性
> 3. 从简单案例开始
> 4. 逐步优化性能
> 5. 集成MLOps工具

---

*本知识库由AI辅助整理，供离线阅读和学习使用。*
