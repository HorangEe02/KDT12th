# 🏭 소주제 D. 설비 고장 유형 예측 — 상세 구현 가이드라인

> **Claude Code에서 단계별로 실행할 수 있는 구현 명세서**
>
> 핵심 기술: LSTM + BERT 텍스트/수치 분류 + 클래스 불균형 처리 + 모델 비교

---

## 목차

1. [환경 설정](#1-환경-설정)
2. [데이터 다운로드 및 탐색](#2-데이터-다운로드-및-탐색)
3. [데이터 전처리 — 특성 공학 및 텍스트 생성](#3-데이터-전처리--특성-공학-및-텍스트-생성)
4. [접근법 1: LSTM 기반 시퀀스 분류](#4-접근법-1-lstm-기반-시퀀스-분류)
5. [접근법 2: BERT 기반 텍스트 분류](#5-접근법-2-bert-기반-텍스트-분류)
6. [접근법 3: 수치 특성 기반 DNN 분류 (베이스라인)](#6-접근법-3-수치-특성-기반-dnn-분류-베이스라인)
7. [모델 비교 및 종합 분석](#7-모델-비교-및-종합-분석)
8. [시각화 및 해석](#8-시각화-및-해석)
9. [결과 저장 및 정리](#9-결과-저장-및-정리)

---

## 1. 환경 설정

### 1.1 프로젝트 디렉토리 생성

```bash
mkdir -p SubTopic_D_Maintenance_NLP/{data,notebooks,models,results}
cd SubTopic_D_Maintenance_NLP
```

### 1.2 필수 패키지 설치

```bash
pip install torch torchvision transformers datasets tokenizers
pip install matplotlib seaborn scikit-learn pandas numpy tqdm wordcloud
```

### 1.3 requirements.txt

```text
torch>=2.0.0
transformers>=4.35.0
datasets>=2.14.0
tokenizers>=0.15.0
matplotlib>=3.7.0
seaborn>=0.12.0
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
tqdm>=4.65.0
wordcloud>=1.9.0
```

### 1.4 환경 확인

```python
import torch
import transformers

print(f"PyTorch: {torch.__version__}")
print(f"Transformers: {transformers.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {device}")
```

---

## 2. 데이터 다운로드 및 탐색

### 2.1 데이터셋 정보

| 항목       | 내용                                                                                  |
| ---------- | ------------------------------------------------------------------------------------- |
| 데이터셋명 | Machine Predictive Maintenance Classification                                         |
| 출처       | https://www.kaggle.com/datasets/shivamb/machine-predictive-maintenance-classification |
| 레코드 수  | 10,000건                                                                              |
| 특성 수    | 8개 (수치 + 범주)                                                                     |
| 타겟 변수  | Failure Type (고장 유형 5종 + No Failure)                                             |
| 특이사항   | 수치 데이터를 텍스트로 변환하여 NLP 적용 가능                                         |

### 2.2 다운로드

```bash
# Kaggle API
kaggle datasets download -d shivamb/machine-predictive-maintenance-classification
unzip machine-predictive-maintenance-classification.zip -d data/
```

### 2.3 데이터 구조 분석

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# === 데이터 로드 ===
df = pd.read_csv("data/predictive_maintenance.csv")
print(f"데이터 크기: {df.shape}")
print(f"\n컬럼 목록:")
print(df.dtypes)
print(f"\n처음 5행:")
print(df.head())
```

### 2.4 컬럼 설명

```
┌─────────────────────────────────────────────────────────────────────┐
│  컬럼 설명                                                          │
├──────────────────┬──────────────────────────────────────────────────┤
│ UDI              │ 고유 식별자 (1~10000)                             │
│ Product ID       │ 제품 ID (L/M/H + 번호) — 품질 등급 포함            │
│ Type             │ 제품 품질 등급 (L=Low, M=Medium, H=High)          │
│ Air temperature  │ 공기 온도 [K] (켈빈)                              │
│ Process temp     │ 공정 온도 [K]                                     │
│ Rotational speed │ 회전 속도 [rpm]                                   │
│ Torque           │ 토크 [Nm] (뉴턴미터)                              │
│ Tool wear        │ 공구 마모도 [min] (사용 시간)                      │
│ Target           │ 고장 여부 (0=정상, 1=고장) — 이진 분류용            │
│ Failure Type     │ 고장 유형 — 다중 분류용 (핵심 타겟)                │
└──────────────────┴──────────────────────────────────────────────────┘

Failure Type 클래스:
  • No Failure           — 고장 없음 (대다수)
  • Heat Dissipation F.  — 열 방출 고장
  • Power Failure        — 전력 고장
  • Overstrain Failure   — 과부하 고장
  • Tool Wear Failure    — 공구 마모 고장
  • Random Failures      — 무작위 고장
```

### 2.5 EDA 시각화

```python
# === 고장 유형 분포 ===
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 1) 고장 유형별 빈도
failure_counts = df['Failure Type'].value_counts()
colors = ['#2ecc71', '#e74c3c', '#f39c12', '#3498db', '#9b59b6', '#1abc9c']
bars = axes[0].barh(failure_counts.index, failure_counts.values, color=colors)
axes[0].set_xlabel('건수')
axes[0].set_title('고장 유형별 분포', fontweight='bold')
for bar, val in zip(bars, failure_counts.values):
    axes[0].text(val + 30, bar.get_y() + bar.get_height()/2,
                 f'{val} ({val/len(df)*100:.1f}%)', va='center', fontsize=9)

# 2) 수치 특성 분포 (온도, 회전속도, 토크, 마모도)
numeric_cols = ['Air temperature [K]', 'Process temperature [K]',
                'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']
df[numeric_cols].hist(ax=axes[1], bins=30, color='#3498db', alpha=0.7, layout=(1,5))
axes[1].set_title('수치 특성 분포', fontweight='bold')

# 3) 품질 등급별 고장률
type_failure = df.groupby('Type')['Target'].mean() * 100
axes[2].bar(type_failure.index, type_failure.values, color=['#2ecc71', '#f39c12', '#e74c3c'])
axes[2].set_ylabel('고장률 (%)')
axes[2].set_title('품질 등급별 고장률', fontweight='bold')
for i, v in enumerate(type_failure.values):
    axes[2].text(i, v + 0.3, f'{v:.1f}%', ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig("results/01_eda_overview.png", dpi=150, bbox_inches='tight')
plt.show()

# === 클래스 불균형 확인 ===
print(f"\n=== 클래스 불균형 ===")
for ft, count in failure_counts.items():
    print(f"  {ft:<30s}: {count:>5d} ({count/len(df)*100:>5.1f}%)")
print(f"\n→ 'No Failure'가 ~96%로 극심한 불균형!")

# === 고장 유형별 수치 특성 비교 ===
fig, axes = plt.subplots(1, 4, figsize=(20, 5))
plot_cols = ['Air temperature [K]', 'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']

for idx, col in enumerate(plot_cols):
    df.boxplot(column=col, by='Failure Type', ax=axes[idx], rot=45)
    axes[idx].set_title(col, fontsize=9, fontweight='bold')
    axes[idx].set_xlabel('')

plt.suptitle('고장 유형별 수치 특성 비교', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig("results/02_feature_by_failure.png", dpi=150, bbox_inches='tight')
plt.show()
```

---

## 3. 데이터 전처리 — 특성 공학 및 텍스트 생성

### 3.1 핵심 전략: 수치 데이터 → 텍스트 변환

```
왜 수치 데이터를 텍스트로 변환하는가?

  이 프로젝트의 핵심 목표는 "NLP 기법을 제조 데이터에 적용"하는 것입니다.
  센서 수치 데이터를 자연어 설명문으로 변환하면:

  1. BERT/LSTM 같은 NLP 모델을 직접 적용할 수 있음
  2. "온도가 높고 토크가 강하며 마모가 심하다" 같은 의미적 맥락을 학습
  3. 실제 현장에서 작업자가 작성하는 설비 로그와 유사한 형태

  변환 예시:
  수치: Air_temp=305.3, Process_temp=311.2, RPM=1312, Torque=52.4, Wear=215
  텍스트: "Type M machine. Air temperature 305.3K (high). Process temperature
           311.2K (high). Rotational speed 1312rpm (low). Torque 52.4Nm (high).
           Tool wear 215min (severe). Temperature difference 5.9K."
```

### 3.2 텍스트 변환 함수

```python
def row_to_text(row):
    """
    센서 수치 데이터를 자연어 설명문으로 변환

    각 수치를 의미 있는 범주(low/normal/high/severe)로 태깅하여
    NLP 모델이 패턴을 학습할 수 있는 맥락 정보를 제공
    """

    # 온도 범주화
    air_temp = row['Air temperature [K]']
    air_level = 'low' if air_temp < 298 else ('normal' if air_temp < 302 else 'high')

    proc_temp = row['Process temperature [K]']
    proc_level = 'low' if proc_temp < 308 else ('normal' if proc_temp < 311 else 'high')

    # 회전 속도 범주화
    rpm = row['Rotational speed [rpm]']
    rpm_level = 'low' if rpm < 1300 else ('normal' if rpm < 1600 else 'high')

    # 토크 범주화
    torque = row['Torque [Nm]']
    torque_level = 'low' if torque < 30 else ('normal' if torque < 50 else 'high')

    # 공구 마모도 범주화
    wear = row['Tool wear [min]']
    wear_level = 'minimal' if wear < 50 else ('moderate' if wear < 150 else 'severe')

    # 파생 특성
    temp_diff = abs(proc_temp - air_temp)
    power = torque * rpm * 2 * 3.14159 / 60  # 대략적 전력

    text = (
        f"Type {row['Type']} machine. "
        f"Air temperature {air_temp:.1f}K ({air_level}). "
        f"Process temperature {proc_temp:.1f}K ({proc_level}). "
        f"Rotational speed {rpm}rpm ({rpm_level}). "
        f"Torque {torque:.1f}Nm ({torque_level}). "
        f"Tool wear {wear}min ({wear_level}). "
        f"Temperature difference {temp_diff:.1f}K. "
        f"Estimated power {power:.0f}W."
    )

    return text


# === 텍스트 변환 실행 ===
df['text'] = df.apply(row_to_text, axis=1)

# 확인
print("=== 텍스트 변환 예시 ===")
for i in range(3):
    print(f"\n[{df.iloc[i]['Failure Type']}]")
    print(f"  {df.iloc[i]['text'][:120]}...")
```

### 3.3 라벨 인코딩 및 데이터 분리

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# === 라벨 인코딩 ===
le = LabelEncoder()
df['label'] = le.fit_transform(df['Failure Type'])
LABEL_NAMES = list(le.classes_)
NUM_CLASSES = len(LABEL_NAMES)

print(f"클래스 매핑:")
for idx, name in enumerate(LABEL_NAMES):
    count = (df['label'] == idx).sum()
    print(f"  {idx}: {name} ({count}건)")

# === Train / Val / Test 분리 (7:1.5:1.5) ===
train_df, temp_df = train_test_split(df, test_size=0.3, random_state=42,
                                      stratify=df['label'])
val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42,
                                    stratify=temp_df['label'])

print(f"\nTrain: {len(train_df)} / Val: {len(val_df)} / Test: {len(test_df)}")

# 분리 후 클래스 분포 확인
for split_name, split_df in [('Train', train_df), ('Val', val_df), ('Test', test_df)]:
    dist = split_df['label'].value_counts().sort_index()
    print(f"  {split_name}: {dict(dist)}")
```

---

## 4. 접근법 1: LSTM 기반 시퀀스 분류

### 4.1 토큰화 및 Dataset

```python
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from collections import Counter

# === 단어 사전 구축 ===
def build_vocab(texts, min_freq=1):
    """텍스트에서 단어 사전 구축"""
    counter = Counter()
    for text in texts:
        counter.update(text.lower().split())

    vocab = {'<PAD>': 0, '<UNK>': 1}
    idx = 2
    for word, freq in counter.most_common():
        if freq >= min_freq:
            vocab[word] = idx
            idx += 1

    print(f"어휘 사전 크기: {len(vocab)}")
    return vocab

vocab = build_vocab(train_df['text'].tolist())

# === 텍스트 → 인덱스 시퀀스 변환 ===
def text_to_indices(text, vocab, max_len=128):
    """텍스트를 정수 인덱스 시퀀스로 변환 (패딩 포함)"""
    tokens = text.lower().split()
    indices = [vocab.get(t, vocab['<UNK>']) for t in tokens]

    # 패딩 또는 자르기
    if len(indices) < max_len:
        indices += [vocab['<PAD>']] * (max_len - len(indices))
    else:
        indices = indices[:max_len]

    return indices

MAX_LEN = 128

class MaintenanceDataset(Dataset):
    """설비 유지보수 텍스트 분류 데이터셋"""

    def __init__(self, dataframe, vocab, max_len=128):
        self.texts = dataframe['text'].tolist()
        self.labels = dataframe['label'].tolist()
        self.vocab = vocab
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        indices = text_to_indices(self.texts[idx], self.vocab, self.max_len)
        return (
            torch.tensor(indices, dtype=torch.long),
            torch.tensor(self.labels[idx], dtype=torch.long)
        )

# === DataLoader 생성 ===
BATCH_SIZE = 32

train_dataset = MaintenanceDataset(train_df, vocab, MAX_LEN)
val_dataset = MaintenanceDataset(val_df, vocab, MAX_LEN)
test_dataset = MaintenanceDataset(test_df, vocab, MAX_LEN)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

# 확인
x, y = next(iter(train_loader))
print(f"입력: {x.shape}, 라벨: {y.shape}")  # (32, 128), (32,)
```

### 4.2 LSTM 모델 정의

```python
class LSTMClassifier(nn.Module):
    """
    Bi-LSTM 텍스트 분류 모델

    구조: Embedding → Bi-LSTM → Attention Pooling → FC → 출력

    수업 연결:
      - 01_순환_신경망_RNN_LSTM_통합.md의 LSTM 게이트 메커니즘
      - 양방향(Bidirectional)으로 전후 문맥을 모두 활용
    """

    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256,
                 num_classes=6, num_layers=2, dropout=0.3):
        super().__init__()

        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,    # 양방향 LSTM
            dropout=dropout
        )
        # 양방향이므로 hidden_dim * 2
        self.attention = nn.Linear(hidden_dim * 2, 1)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        # x: (batch, seq_len)
        embedded = self.embedding(x)           # (batch, seq_len, embed_dim)
        lstm_out, _ = self.lstm(embedded)       # (batch, seq_len, hidden*2)

        # Attention Pooling: 중요한 시점에 더 큰 가중치
        attn_weights = torch.softmax(
            self.attention(lstm_out).squeeze(-1), dim=1
        )                                       # (batch, seq_len)
        context = torch.bmm(
            attn_weights.unsqueeze(1), lstm_out
        ).squeeze(1)                            # (batch, hidden*2)

        return self.classifier(context)         # (batch, num_classes)


lstm_model = LSTMClassifier(
    vocab_size=len(vocab),
    embed_dim=128,
    hidden_dim=256,
    num_classes=NUM_CLASSES
).to(device)

total_params = sum(p.numel() for p in lstm_model.parameters())
print(f"LSTM 파라미터: {total_params:,}개")
```

### 4.3 클래스 불균형 처리 — 가중치 적용

```python
# === 클래스 가중치 계산 (역빈도 가중치) ===
class_counts = train_df['label'].value_counts().sort_index().values
class_weights = 1.0 / class_counts
class_weights = class_weights / class_weights.sum() * len(class_counts)
class_weights_tensor = torch.tensor(class_weights, dtype=torch.float32).to(device)

print("클래스 가중치:")
for i, (name, w) in enumerate(zip(LABEL_NAMES, class_weights)):
    print(f"  {name}: {w:.4f}")

# → 'No Failure'(다수): 낮은 가중치
# → 'Tool Wear Failure'(소수): 높은 가중치
```

### 4.4 LSTM 학습

```python
from tqdm import tqdm
import time

def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss, correct, total = 0, 0, 0
    for texts, labels in tqdm(loader, desc="  Train", leave=False):
        texts, labels = texts.to(device), labels.to(device)
        outputs = model(texts)
        loss = criterion(outputs, labels)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()
        total_loss += loss.item() * texts.size(0)
        correct += (outputs.argmax(1) == labels).sum().item()
        total += texts.size(0)
    return total_loss / total, correct / total

def evaluate_epoch(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0, 0, 0
    all_preds, all_labels = [], []
    with torch.no_grad():
        for texts, labels in tqdm(loader, desc="  Eval", leave=False):
            texts, labels = texts.to(device), labels.to(device)
            outputs = model(texts)
            loss = criterion(outputs, labels)
            total_loss += loss.item() * texts.size(0)
            preds = outputs.argmax(1)
            correct += (preds == labels).sum().item()
            total += texts.size(0)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    return total_loss / total, correct / total, np.array(all_preds), np.array(all_labels)


# === LSTM 학습 실행 ===
criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
optimizer = torch.optim.Adam(lstm_model.parameters(), lr=1e-3, weight_decay=1e-5)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='max', factor=0.5, patience=3, verbose=True
)

NUM_EPOCHS = 20
lstm_history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
best_val_acc = 0
start = time.time()

for epoch in range(NUM_EPOCHS):
    print(f"\nEpoch [{epoch+1}/{NUM_EPOCHS}]")
    tl, ta = train_epoch(lstm_model, train_loader, criterion, optimizer, device)
    vl, va, _, _ = evaluate_epoch(lstm_model, val_loader, criterion, device)
    scheduler.step(va)

    lstm_history['train_loss'].append(tl)
    lstm_history['train_acc'].append(ta)
    lstm_history['val_loss'].append(vl)
    lstm_history['val_acc'].append(va)

    print(f"  Train — Loss: {tl:.4f} | Acc: {ta:.4f}")
    print(f"  Val   — Loss: {vl:.4f} | Acc: {va:.4f}")

    if va > best_val_acc:
        best_val_acc = va
        torch.save(lstm_model.state_dict(), "models/best_lstm.pth")
        print(f"  ★ Best 저장! (Val Acc: {va:.4f})")

print(f"\nLSTM 완료! {(time.time()-start)/60:.1f}분 | Best Val Acc: {best_val_acc:.4f}")
lstm_model.load_state_dict(torch.load("models/best_lstm.pth"))
```

---

## 5. 접근법 2: BERT 기반 텍스트 분류

### 5.1 BERT 토큰화 및 Dataset

```python
from transformers import (
    BertTokenizerFast, BertForSequenceClassification,
    Trainer, TrainingArguments
)
from datasets import Dataset as HFDataset

# === DistilBERT 사용 (경량 BERT, 학습 속도 2배) ===
MODEL_NAME = "distilbert-base-uncased"
tokenizer = BertTokenizerFast.from_pretrained(MODEL_NAME)

# === HuggingFace Dataset 형식 변환 ===
def make_hf_dataset(dataframe):
    return HFDataset.from_dict({
        'text': dataframe['text'].tolist(),
        'label': dataframe['label'].tolist()
    })

train_hf = make_hf_dataset(train_df)
val_hf = make_hf_dataset(val_df)
test_hf = make_hf_dataset(test_df)

# === 토큰화 ===
def tokenize_fn(examples):
    return tokenizer(
        examples['text'],
        truncation=True,
        padding='max_length',
        max_length=128
    )

train_tokenized = train_hf.map(tokenize_fn, batched=True)
val_tokenized = val_hf.map(tokenize_fn, batched=True)
test_tokenized = test_hf.map(tokenize_fn, batched=True)

# PyTorch 텐서로 설정
train_tokenized.set_format('torch', columns=['input_ids', 'attention_mask', 'label'])
val_tokenized.set_format('torch', columns=['input_ids', 'attention_mask', 'label'])
test_tokenized.set_format('torch', columns=['input_ids', 'attention_mask', 'label'])

print(f"토큰화 완료!")
print(f"  Train: {len(train_tokenized)}")
print(f"  Val: {len(val_tokenized)}")
print(f"  Test: {len(test_tokenized)}")
```

### 5.2 BERT 모델 학습 (HuggingFace Trainer)

```python
from sklearn.metrics import accuracy_score, f1_score

# === 모델 로드 ===
bert_model = BertForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=NUM_CLASSES
)

# === 평가 메트릭 ===
def compute_metrics(eval_pred):
    preds = eval_pred.predictions.argmax(-1)
    labels = eval_pred.label_ids
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average='macro')
    return {'accuracy': acc, 'f1_macro': f1}

# === 학습 설정 ===
training_args = TrainingArguments(
    output_dir="models/bert_output",
    num_train_epochs=5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    learning_rate=2e-5,
    weight_decay=0.01,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1_macro",
    logging_steps=50,
    report_to="none",           # wandb 비활성화
    fp16=torch.cuda.is_available(),  # GPU면 Mixed Precision
)

# === Trainer 생성 및 학습 ===
trainer = Trainer(
    model=bert_model,
    args=training_args,
    train_dataset=train_tokenized,
    eval_dataset=val_tokenized,
    compute_metrics=compute_metrics,
)

print("\n=== BERT (DistilBERT) 학습 시작 ===")
trainer.train()

# === 학습 기록 추출 ===
bert_history = trainer.state.log_history
print("\nBERT 학습 완료!")
```

### 5.3 BERT 테스트 평가

```python
# === 테스트 셋 평가 ===
bert_test_results = trainer.evaluate(test_tokenized)
print(f"\n=== BERT 테스트 성능 ===")
for k, v in bert_test_results.items():
    if 'accuracy' in k or 'f1' in k or 'loss' in k:
        print(f"  {k}: {v:.4f}")

# === 예측값 추출 ===
bert_predictions = trainer.predict(test_tokenized)
bert_preds = bert_predictions.predictions.argmax(-1)
bert_labels = bert_predictions.label_ids
```

---

## 6. 접근법 3: 수치 특성 기반 DNN 분류 (베이스라인)

### 6.1 수치 DNN 모델 (NLP 없는 베이스라인)

```python
from sklearn.preprocessing import StandardScaler

# === 수치 특성 추출 ===
feature_cols = ['Air temperature [K]', 'Process temperature [K]',
                'Rotational speed [rpm]', 'Torque [Nm]', 'Tool wear [min]']

# 파생 특성 추가
df['temp_diff'] = df['Process temperature [K]'] - df['Air temperature [K]']
df['power'] = df['Torque [Nm]'] * df['Rotational speed [rpm]'] * 2 * 3.14159 / 60
df['type_encoded'] = df['Type'].map({'L': 0, 'M': 1, 'H': 2})
extended_cols = feature_cols + ['temp_diff', 'power', 'type_encoded']

# 스케일링
scaler = StandardScaler()
X_train = scaler.fit_transform(train_df[extended_cols])
X_val = scaler.transform(val_df[extended_cols])
X_test = scaler.transform(test_df[extended_cols])

y_train = train_df['label'].values
y_val = val_df['label'].values
y_test = test_df['label'].values


class DNNClassifier(nn.Module):
    """수치 특성 기반 DNN (NLP 비교용 베이스라인)"""
    def __init__(self, input_dim, num_classes=6):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.BatchNorm1d(64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, 32), nn.ReLU(),
            nn.Linear(32, num_classes)
        )
    def forward(self, x):
        return self.net(x)


# === Dataset / DataLoader ===
from torch.utils.data import TensorDataset

train_tensor = TensorDataset(torch.tensor(X_train, dtype=torch.float32),
                             torch.tensor(y_train, dtype=torch.long))
val_tensor = TensorDataset(torch.tensor(X_val, dtype=torch.float32),
                           torch.tensor(y_val, dtype=torch.long))
test_tensor = TensorDataset(torch.tensor(X_test, dtype=torch.float32),
                            torch.tensor(y_test, dtype=torch.long))

dnn_train_loader = DataLoader(train_tensor, batch_size=64, shuffle=True)
dnn_val_loader = DataLoader(val_tensor, batch_size=64, shuffle=False)
dnn_test_loader = DataLoader(test_tensor, batch_size=64, shuffle=False)

# === 학습 ===
dnn_model = DNNClassifier(len(extended_cols), NUM_CLASSES).to(device)
dnn_criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
dnn_optimizer = torch.optim.Adam(dnn_model.parameters(), lr=1e-3)

for epoch in range(30):
    dnn_model.train()
    for xb, yb in dnn_train_loader:
        xb, yb = xb.to(device), yb.to(device)
        loss = dnn_criterion(dnn_model(xb), yb)
        dnn_optimizer.zero_grad()
        loss.backward()
        dnn_optimizer.step()

# === 평가 ===
dnn_model.eval()
dnn_preds, dnn_labels = [], []
with torch.no_grad():
    for xb, yb in dnn_test_loader:
        preds = dnn_model(xb.to(device)).argmax(1).cpu()
        dnn_preds.extend(preds.numpy())
        dnn_labels.extend(yb.numpy())

dnn_preds = np.array(dnn_preds)
dnn_labels = np.array(dnn_labels)
print(f"DNN Accuracy: {accuracy_score(dnn_labels, dnn_preds):.4f}")
print(f"DNN F1 (macro): {f1_score(dnn_labels, dnn_preds, average='macro'):.4f}")
```

---

## 7. 모델 비교 및 종합 분석

### 7.1 3개 모델 테스트 성능 비교

```python
from sklearn.metrics import classification_report, confusion_matrix

# === LSTM 테스트 평가 ===
_, lstm_acc, lstm_preds, lstm_labels = evaluate_epoch(
    lstm_model, test_loader, criterion, device
)

# === 3모델 성능 비교 ===
models_eval = {
    'DNN (수치)': {'preds': dnn_preds, 'labels': dnn_labels},
    'LSTM (텍스트)': {'preds': lstm_preds, 'labels': lstm_labels},
    'BERT (텍스트)': {'preds': bert_preds, 'labels': bert_labels},
}

print(f"\n{'='*70}")
print(f"{'3개 모델 최종 성능 비교':^70}")
print(f"{'='*70}")
print(f"{'모델':<20} {'Accuracy':>10} {'F1 (macro)':>12} {'F1 (weighted)':>14}")
print(f"{'-'*70}")

comparison = {}
for name, data in models_eval.items():
    acc = accuracy_score(data['labels'], data['preds'])
    f1_mac = f1_score(data['labels'], data['preds'], average='macro')
    f1_wgt = f1_score(data['labels'], data['preds'], average='weighted')
    comparison[name] = {'accuracy': acc, 'f1_macro': f1_mac, 'f1_weighted': f1_wgt}
    print(f"{name:<20} {acc:>10.4f} {f1_mac:>12.4f} {f1_wgt:>14.4f}")

best = max(comparison, key=lambda x: comparison[x]['f1_macro'])
print(f"\n🏆 최고 F1(macro) 모델: {best}")
```

### 7.2 혼동행렬 비교

```python
fig, axes = plt.subplots(1, 3, figsize=(20, 5.5))

for idx, (name, data) in enumerate(models_eval.items()):
    cm = confusion_matrix(data['labels'], data['preds'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                xticklabels=LABEL_NAMES, yticklabels=LABEL_NAMES)
    axes[idx].set_title(f'{name}\nAcc: {comparison[name]["accuracy"]:.1%}',
                        fontweight='bold', fontsize=10)
    axes[idx].set_xlabel('Predicted')
    axes[idx].set_ylabel('Actual')
    axes[idx].tick_params(axis='both', labelsize=6)
    plt.setp(axes[idx].get_xticklabels(), rotation=45, ha='right')

plt.suptitle('3모델 혼동행렬 비교', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig("results/05_confusion_matrices.png", dpi=150, bbox_inches='tight')
plt.show()
```

---

## 8. 시각화 및 해석

### 8.1 학습 곡선

```python
def plot_lstm_curves(history, save_path="results/03_lstm_training_curves.png"):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    ep = range(1, len(history['train_loss']) + 1)

    axes[0].plot(ep, history['train_loss'], 'b--', alpha=0.7, label='Train')
    axes[0].plot(ep, history['val_loss'], 'r-', label='Val')
    axes[0].set_title('LSTM Loss', fontweight='bold')
    axes[0].legend(); axes[0].grid(True, alpha=0.3)

    axes[1].plot(ep, history['train_acc'], 'b--', alpha=0.7, label='Train')
    axes[1].plot(ep, history['val_acc'], 'r-', label='Val')
    axes[1].set_title('LSTM Accuracy', fontweight='bold')
    axes[1].legend(); axes[1].grid(True, alpha=0.3)

    plt.suptitle('LSTM 학습 곡선', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_lstm_curves(lstm_history)
```

### 8.2 클래스별 Classification Report

```python
best_name = max(comparison, key=lambda x: comparison[x]['f1_macro'])
best_data = models_eval[best_name]

print(f"\n=== {best_name} — 상세 Classification Report ===\n")
print(classification_report(
    best_data['labels'], best_data['preds'],
    target_names=LABEL_NAMES, digits=4
))
```

### 8.3 성능 비교 막대그래프

```python
def plot_comparison(comparison, save_path="results/06_model_comparison.png"):
    fig, ax = plt.subplots(figsize=(10, 5))
    models = list(comparison.keys())
    x = np.arange(len(models))
    w = 0.25

    acc = [comparison[m]['accuracy'] for m in models]
    f1m = [comparison[m]['f1_macro'] for m in models]
    f1w = [comparison[m]['f1_weighted'] for m in models]

    ax.bar(x - w, acc, w, label='Accuracy', color='#3498db')
    ax.bar(x, f1m, w, label='F1 (macro)', color='#e74c3c')
    ax.bar(x + w, f1w, w, label='F1 (weighted)', color='#2ecc71')

    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 1.05)
    ax.set_title('DNN vs LSTM vs BERT — 성능 비교', fontweight='bold')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    for i, (a, fm, fw) in enumerate(zip(acc, f1m, f1w)):
        ax.text(i - w, a + 0.02, f'{a:.3f}', ha='center', fontsize=7)
        ax.text(i, fm + 0.02, f'{fm:.3f}', ha='center', fontsize=7)
        ax.text(i + w, fw + 0.02, f'{fw:.3f}', ha='center', fontsize=7)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_comparison(comparison)
```

### 8.4 텍스트 워드클라우드 (고장 유형별)

```python
from wordcloud import WordCloud

def plot_wordclouds(df, save_path="results/07_wordclouds.png"):
    """고장 유형별 텍스트 워드클라우드"""
    failure_types = [ft for ft in df['Failure Type'].unique() if ft != 'No Failure']

    fig, axes = plt.subplots(1, len(failure_types), figsize=(5 * len(failure_types), 4))

    for idx, ft in enumerate(failure_types):
        texts = ' '.join(df[df['Failure Type'] == ft]['text'].tolist())
        wc = WordCloud(width=400, height=300, background_color='white',
                      colormap='Reds', max_words=50).generate(texts)
        axes[idx].imshow(wc, interpolation='bilinear')
        axes[idx].set_title(ft, fontsize=9, fontweight='bold')
        axes[idx].axis('off')

    plt.suptitle('고장 유형별 핵심 키워드 (워드클라우드)', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()

plot_wordclouds(df)
```

---

## 9. 결과 저장 및 정리

### 9.1 결과 JSON 저장

```python
import json

summary = {
    "project": "설비 고장 유형 예측 (NLP)",
    "dataset": "Machine Predictive Maintenance (10,000건)",
    "num_classes": NUM_CLASSES,
    "classes": LABEL_NAMES,
    "approach": "수치→텍스트 변환 후 NLP 모델 적용",
    "model_comparison": {
        name: {k: round(float(v), 4) for k, v in metrics.items()}
        for name, metrics in comparison.items()
    },
    "best_model": best_name,
    "key_insight": "BERT/LSTM이 수치 DNN 대비 고장 유형 분류에서 어떤 이점을 보이는지 비교"
}

with open("results/08_final_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("저장 완료: results/08_final_summary.json")
```

### 9.2 최종 출력 파일 목록

```
results/
├── 01_eda_overview.png            ← 고장 분포 + 특성 분포 + 등급별 고장률
├── 02_feature_by_failure.png      ← 고장 유형별 수치 특성 박스플롯
├── 03_lstm_training_curves.png    ← LSTM 학습 곡선
├── 04_bert_training_log.txt       ← BERT 학습 로그 (Trainer 자동)
├── 05_confusion_matrices.png      ← DNN/LSTM/BERT 혼동행렬 비교
├── 06_model_comparison.png        ← 3모델 성능 막대그래프
├── 07_wordclouds.png              ← 고장 유형별 워드클라우드
└── 08_final_summary.json          ← 성능 지표 JSON

models/
├── best_lstm.pth                  ← LSTM 가중치
└── bert_output/                   ← BERT 체크포인트 (Trainer 자동)
```

---

## 부록: Claude Code 실행 순서 요약

```
[Step 1] 환경 설정
  → transformers, datasets 설치, GPU 확인

[Step 2] 데이터 탐색
  → 10,000건 로드, 고장 유형 분포, 클래스 불균형 확인

[Step 3] 텍스트 변환
  → 수치 센서 데이터 → 자연어 설명문 변환, 라벨 인코딩

[Step 4] LSTM 학습
  → 어휘 사전 구축 → Bi-LSTM + Attention → 20 에폭 학습

[Step 5] BERT 학습
  → DistilBERT 토큰화 → HuggingFace Trainer → 5 에폭 학습

[Step 6] DNN 베이스라인
  → 수치 특성 + 파생 특성 → DNN 분류기 → 30 에폭 학습

[Step 7] 3모델 비교
  → Accuracy, F1(macro/weighted), 혼동행렬 비교

[Step 8] 시각화
  → 학습 곡선, 성능 비교, 워드클라우드

[Step 9] 결과 저장
  → JSON 요약, 그래프 이미지
```

### 예상 소요 시간

| 단계                | GPU (Colab T4) |    CPU Only    |
| ------------------- | :------------: | :------------: |
| 데이터 준비 + EDA   |      5분       |      5분       |
| LSTM 학습 (20 에폭) |     5~10분     |    20~30분     |
| BERT 학습 (5 에폭)  |    10~15분     |    1~2시간     |
| DNN 베이스라인      |      2분       |      5분       |
| 평가 + 시각화       |      5분       |      5분       |
| **총 소요 시간**    | **약 30~40분** | **약 2~3시간** |

### 목표 성능 기준

| 지표          | 최소 기준 | 우수 기준 |
| ------------- | :-------: | :-------: |
| Accuracy      |   ≥ 85%   |   ≥ 95%   |
| F1 (macro)    |  ≥ 0.50   |  ≥ 0.75   |
| F1 (weighted) |  ≥ 0.85   |  ≥ 0.95   |

> F1(macro)가 낮은 이유: 극심한 클래스 불균형(No Failure 96%)으로 인해 소수 고장 유형의 F1이 낮기 때문입니다. F1(macro) 0.50 이상이면 소수 클래스도 의미 있게 분류하고 있다는 뜻입니다.

### 소주제 A·B·C와의 핵심 차이점

| 비교 항목   |   A (분류)   | B (세그먼테이션) |  C (객체탐지)   |       D (NLP)        |
| ----------- | :----------: | :--------------: | :-------------: | :------------------: |
| 입력 데이터 |    이미지    |      이미지      |     이미지      |      **텍스트**      |
| 모델        |  ResNet/VGG  |      U-Net       |     YOLOv8      |    **LSTM/BERT**     |
| 프레임워크  |   PyTorch    |     PyTorch      |   Ultralytics   |   **HuggingFace**    |
| 평가 지표   | Accuracy, F1 |    Dice, IoU     |       mAP       |    **F1 (macro)**    |
| 핵심 난이도 |  모델 비교   |  클래스 불균형   | 어노테이션 변환 | **수치→텍스트 변환** |
| 수업 연결   | CNN 전이학습 |    U-Net 구조    | YOLO 워크플로우 |  **BERT 파인튜닝**   |
