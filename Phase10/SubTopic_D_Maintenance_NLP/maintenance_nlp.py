#!/usr/bin/env python3
"""
소주제 D. 설비 고장 유형 예측
==============================
AI 기반 스마트 팩토리 품질관리 시스템 — LSTM / BERT / DNN 비교

핵심: 센서 수치 → 자연어 텍스트 변환 → NLP 모델 분류

파이프라인:
  1. 환경 설정
  2. 데이터 로드 및 EDA
  3. 피처 엔지니어링 + 수치→텍스트 변환
  4. LSTM (Bi-LSTM + Attention, 20 epochs)
  5. BERT (DistilBERT, 5 epochs)
  6. DNN 베이스라인 (30 epochs)
  7. 3모델 비교 및 혼동행렬
  8. 워드클라우드 + 결과 저장

실행:
  python maintenance_nlp.py
"""

import os
import json
import random
import math
import warnings
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, TensorDataset

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report

from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
)
# 'datasets' / 'accelerate' 패키지 불필요
# → BERTDataset + 순수 PyTorch 학습 루프로 대체

warnings.filterwarnings("ignore")
matplotlib.rc("font", family="AppleGothic")
matplotlib.rcParams["axes.unicode_minus"] = False

# ============================================================
# 설정
# ============================================================
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)

NUM_WORKERS = 2
NUM_CLASSES = 6
LSTM_EPOCHS = 20
BERT_EPOCHS = 5
DNN_EPOCHS = 30

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "predictive_maintenance.csv"
MODEL_DIR = BASE_DIR / "models"
RESULT_DIR = BASE_DIR / "results"

_SHORT_MAP = {
    "Heat Dissipation Failure": "Heat", "No Failure": "No Fail",
    "Overstrain Failure": "Overstrain", "Power Failure": "Power",
    "Random Failures": "Random", "Tool Wear Failure": "Tool Wear",
}
# SHORT_NAMES는 prepare_data()에서 LabelEncoder 순서에 맞게 동적 생성


# ============================================================
# 1. 환경 설정
# ============================================================
def setup_environment():
    if torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
        print("  Apple Silicon MPS")
    else:
        device = torch.device("cpu")
        print("  CPU 사용")
    print(f"  PyTorch: {torch.__version__}")
    return device


# ============================================================
# 2. EDA
# ============================================================
def load_and_explore(device):
    df = pd.read_csv(DATA_PATH)
    print(f"  Shape: {df.shape}, 결측치: {df.isnull().sum().sum()}")
    print(f"\n  Failure Type 분포:")
    for ft, cnt in df["Failure Type"].value_counts().items():
        print(f"    {ft:<30s}: {cnt:>5} ({cnt/len(df)*100:.2f}%)")

    # EDA 시각화
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    ft_counts = df["Failure Type"].value_counts()
    bars = axes[0, 0].barh(range(len(ft_counts)), ft_counts.values,
                           color=sns.color_palette("Set2", len(ft_counts)))
    axes[0, 0].set_yticks(range(len(ft_counts)))
    axes[0, 0].set_yticklabels(ft_counts.index, fontsize=9)
    axes[0, 0].set_title("고장 유형별 분포")
    axes[0, 0].bar_label(bars, padding=3, fontsize=8)

    num_cols = ["Air temperature [K]", "Process temperature [K]",
                "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]"]
    for idx, col in enumerate(num_cols):
        r, c = (idx + 1) // 3, (idx + 1) % 3
        axes[r, c].hist(df[col], bins=30, color="#3498DB", edgecolor="white", alpha=0.8)
        axes[r, c].set_title(col, fontsize=10)
    plt.suptitle("EDA: 데이터 분포", fontsize=14)
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "01_eda_overview.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  저장: 01_eda_overview.png")
    return df


# ============================================================
# 3. 피처 엔지니어링 + 텍스트 변환
# ============================================================
def row_to_text(row):
    air_t = row["Air temperature [K]"]
    proc_t = row["Process temperature [K]"]
    rpm = row["Rotational speed [rpm]"]
    torque = row["Torque [Nm]"]
    wear = row["Tool wear [min]"]
    mtype = row["Type"]

    air_cat = "low" if air_t < 298 else ("high" if air_t >= 302 else "normal")
    proc_cat = "low" if proc_t < 308 else ("high" if proc_t >= 311 else "normal")
    rpm_cat = "low" if rpm < 1300 else ("high" if rpm >= 1600 else "normal")
    torque_cat = "low" if torque < 30 else ("high" if torque >= 50 else "normal")
    wear_cat = "minimal" if wear < 50 else ("severe" if wear >= 150 else "moderate")

    temp_diff = abs(proc_t - air_t)
    power = torque * rpm * 2 * math.pi / 60

    return (
        f"Type {mtype} machine. "
        f"Air temperature {air_t:.1f}K {air_cat}. "
        f"Process temperature {proc_t:.1f}K {proc_cat}. "
        f"Rotational speed {rpm}rpm {rpm_cat}. "
        f"Torque {torque:.1f}Nm {torque_cat}. "
        f"Tool wear {wear}min {wear_cat}. "
        f"Temperature difference {temp_diff:.1f}K. "
        f"Estimated power {power:.0f}W."
    )


def prepare_data(df, device):
    df["text"] = df.apply(row_to_text, axis=1)
    print(f"  샘플 텍스트: {df['text'].iloc[0][:80]}...")

    le = LabelEncoder()
    df["label"] = le.fit_transform(df["Failure Type"])
    label_names = list(le.classes_)
    short_names = [_SHORT_MAP[c] for c in label_names]

    class_counts = df["label"].value_counts().sort_index().values.astype(float)
    class_weights = 1.0 / class_counts
    class_weights = class_weights / class_weights.sum() * NUM_CLASSES
    cw_tensor = torch.FloatTensor(class_weights).to(device)

    train_df, temp_df = train_test_split(df, test_size=0.3, random_state=SEED, stratify=df["label"])
    val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=SEED, stratify=temp_df["label"])
    print(f"  Train: {len(train_df):,}, Val: {len(val_df):,}, Test: {len(test_df):,}")

    # Boxplot
    num_cols = ["Air temperature [K]", "Process temperature [K]",
                "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]"]
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fail_df = df[df["Failure Type"] != "No Failure"]
    for idx, col in enumerate(num_cols):
        ax = axes[idx // 3, idx % 3]
        sns.boxplot(data=fail_df, x="Failure Type", y=col, ax=ax, palette="Set2")
        ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)
        ax.set_title(col, fontsize=10)
    axes[1, 2].axis("off")
    plt.suptitle("고장 유형별 수치 피처 분포", fontsize=14)
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "02_feature_by_failure.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  저장: 02_feature_by_failure.png")

    return df, train_df, val_df, test_df, label_names, short_names, cw_tensor


# ============================================================
# 4. LSTM
# ============================================================
MAX_LEN = 128


def build_vocab(texts, min_freq=1):
    counter = Counter()
    for t in texts:
        counter.update(t.lower().split())
    vocab = {"<PAD>": 0, "<UNK>": 1}
    for w, c in counter.items():
        if c >= min_freq:
            vocab[w] = len(vocab)
    return vocab


def text_to_indices(text, vocab):
    tokens = text.lower().split()[:MAX_LEN]
    indices = [vocab.get(t, 1) for t in tokens]
    return indices + [0] * (MAX_LEN - len(indices))


class MaintenanceDataset(Dataset):
    def __init__(self, texts, labels, vocab):
        self.texts = texts
        self.labels = labels
        self.vocab = vocab

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        indices = text_to_indices(self.texts[idx], self.vocab)
        return torch.tensor(indices, dtype=torch.long), torch.tensor(self.labels[idx], dtype=torch.long)


class LSTMClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim=128, hidden_dim=256,
                 num_layers=2, num_classes=NUM_CLASSES, dropout=0.3):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, num_layers=num_layers,
                            batch_first=True, bidirectional=True, dropout=dropout)
        self.attention = nn.Linear(hidden_dim * 2, 1)
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 128), nn.ReLU(), nn.Dropout(dropout),
            nn.Linear(128, num_classes),
        )

    def forward(self, x):
        emb = self.embedding(x)
        out, _ = self.lstm(emb)
        attn = torch.softmax(self.attention(out).squeeze(-1), dim=1)
        context = torch.bmm(attn.unsqueeze(1), out).squeeze(1)
        return self.classifier(context)


def train_lstm(train_df, val_df, cw_tensor, device):
    vocab = build_vocab(train_df["text"].tolist())
    print(f"  Vocabulary: {len(vocab)}")

    train_ds = MaintenanceDataset(train_df["text"].tolist(), train_df["label"].tolist(), vocab)
    val_ds = MaintenanceDataset(val_df["text"].tolist(), val_df["label"].tolist(), vocab)
    train_dl = DataLoader(train_ds, batch_size=32, shuffle=True, num_workers=NUM_WORKERS)
    val_dl = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=NUM_WORKERS)

    model = LSTMClassifier(len(vocab)).to(device)
    criterion = nn.CrossEntropyLoss(weight=cw_tensor)
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=3)

    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    best_acc = 0.0

    for epoch in range(1, LSTM_EPOCHS + 1):
        model.train()
        tl, tc, tn = 0, 0, 0
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            tl += loss.item() * x.size(0)
            tc += out.argmax(1).eq(y).sum().item()
            tn += x.size(0)

        model.eval()
        vl, vc, vn = 0, 0, 0
        with torch.no_grad():
            for x, y in val_dl:
                x, y = x.to(device), y.to(device)
                out = model(x)
                loss = criterion(out, y)
                vl += loss.item() * x.size(0)
                vc += out.argmax(1).eq(y).sum().item()
                vn += x.size(0)

        t_l, t_a = tl / tn, tc / tn
        v_l, v_a = vl / vn, vc / vn
        scheduler.step(v_a)
        history["train_loss"].append(t_l)
        history["val_loss"].append(v_l)
        history["train_acc"].append(t_a)
        history["val_acc"].append(v_a)

        improved = ""
        if v_a > best_acc:
            best_acc = v_a
            torch.save(model.state_dict(), MODEL_DIR / "best_lstm.pth")
            improved = " ★"
        print(f"    Epoch {epoch:2d}/{LSTM_EPOCHS} | Loss: {t_l:.4f}/{v_l:.4f} | Acc: {t_a:.4f}/{v_a:.4f}{improved}")

    model.load_state_dict(torch.load(MODEL_DIR / "best_lstm.pth", weights_only=True))

    # Curves
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    ep = range(1, len(history["train_loss"]) + 1)
    axes[0].plot(ep, history["train_loss"], "b--", label="Train")
    axes[0].plot(ep, history["val_loss"], "r-", label="Val")
    axes[0].set_title("LSTM Loss"); axes[0].legend(); axes[0].grid(alpha=0.3)
    axes[1].plot(ep, history["train_acc"], "b--", label="Train")
    axes[1].plot(ep, history["val_acc"], "r-", label="Val")
    axes[1].set_title("LSTM Accuracy"); axes[1].legend(); axes[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "03_lstm_training_curves.png", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"    Best Val Acc: {best_acc:.4f}")

    return model, vocab


# ============================================================
# 5. BERT — BERTDataset (datasets 패키지 없이 동작)
# ============================================================
class BERTDataset(Dataset):
    """
    HuggingFace Trainer가 요구하는 __len__ / __getitem__ 구현.
    tokenizer 결과를 미리 일괄 인코딩한 뒤 인덱스로 슬라이싱.
    Trainer는 'labels' 키를 기대하므로 'label' → 'labels' 변환.
    """
    def __init__(self, texts, labels, tokenizer, max_length=128):
        # 전체 텍스트를 한 번에 토크나이즈 (속도 최적화)
        self.encodings = tokenizer(
            list(texts),
            padding="max_length",
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        self.labels = list(labels)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        # Trainer 내부에서 배치 collate 시 'labels' 키 필요
        item = {key: val[idx] for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def train_bert(train_df, val_df, device):
    """
    Trainer / TrainingArguments / accelerate 없이
    순수 PyTorch 루프로 DistilBERT 파인튜닝.
    """
    bert_name = "distilbert-base-uncased"
    tokenizer = AutoTokenizer.from_pretrained(bert_name)

    train_ds = BERTDataset(train_df["text"].tolist(), train_df["label"].tolist(), tokenizer)
    val_ds   = BERTDataset(val_df["text"].tolist(),   val_df["label"].tolist(),   tokenizer)

    train_dl = DataLoader(train_ds, batch_size=16, shuffle=True,  num_workers=0)
    val_dl   = DataLoader(val_ds,   batch_size=32, shuffle=False, num_workers=0)

    model = AutoModelForSequenceClassification.from_pretrained(
        bert_name, num_labels=NUM_CLASSES)
    model = model.to(device)

    optimizer = optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)
    save_path = MODEL_DIR / "best_bert.pth"
    best_f1   = 0.0
    history   = {"train_loss": [], "val_acc": [], "val_f1": []}

    print(f"  DistilBERT 파인튜닝 시작 ({BERT_EPOCHS} epochs, device={device})")

    for epoch in range(1, BERT_EPOCHS + 1):
        # ── 학습 ──────────────────────────────────────────────
        model.train()
        total_loss = 0.0
        for batch in train_dl:
            input_ids      = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels         = batch["labels"].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids,
                            attention_mask=attention_mask,
                            labels=labels)
            loss = outputs.loss
            loss.backward()
            # 그래디언트 클리핑 (BERT 파인튜닝 안정화)
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_dl)

        # ── 검증 ──────────────────────────────────────────────
        model.eval()
        all_preds, all_labels = [], []
        with torch.no_grad():
            for batch in val_dl:
                input_ids      = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                labels         = batch["labels"]
                outputs = model(input_ids=input_ids,
                                attention_mask=attention_mask)
                preds = outputs.logits.argmax(dim=-1).cpu().numpy()
                all_preds.extend(preds)
                all_labels.extend(labels.numpy())

        val_acc = accuracy_score(all_labels, all_preds)
        val_f1  = f1_score(all_labels, all_preds, average="macro", zero_division=0)

        history["train_loss"].append(avg_loss)
        history["val_acc"].append(val_acc)
        history["val_f1"].append(val_f1)

        improved = ""
        if val_f1 > best_f1:
            best_f1 = val_f1
            torch.save(model.state_dict(), save_path)
            improved = " ★"

        print(f"    Epoch {epoch:2d}/{BERT_EPOCHS} | "
              f"Loss: {avg_loss:.4f} | "
              f"Val Acc: {val_acc:.4f} | "
              f"Val F1(macro): {val_f1:.4f}{improved}")

    # 최고 모델 복원
    model.load_state_dict(torch.load(save_path, weights_only=True))
    print(f"    Best Val F1(macro): {best_f1:.4f}")

    # 학습 곡선 저장
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    ep = range(1, len(history["train_loss"]) + 1)
    axes[0].plot(ep, history["train_loss"], "b-o", markersize=4)
    axes[0].set_title("BERT Train Loss"); axes[0].set_xlabel("Epoch")
    axes[0].grid(alpha=0.3)
    axes[1].plot(ep, history["val_f1"], "r-o", markersize=4, label="F1(macro)")
    axes[1].plot(ep, history["val_acc"], "g--o", markersize=4, label="Accuracy")
    axes[1].set_title("BERT Val Metrics"); axes[1].set_xlabel("Epoch")
    axes[1].legend(); axes[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "03b_bert_curves.png", dpi=150, bbox_inches="tight")
    plt.close()

    return model, tokenizer


# ============================================================
# 6. DNN
# ============================================================
def prepare_numeric(dataframe):
    feat = dataframe[["Air temperature [K]", "Process temperature [K]",
                      "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]"]].copy()
    feat["temp_diff"] = feat["Process temperature [K]"] - feat["Air temperature [K]"]
    feat["power"] = feat["Torque [Nm]"] * feat["Rotational speed [rpm]"] * 2 * math.pi / 60
    feat["type_encoded"] = dataframe["Type"].map({"L": 0, "M": 1, "H": 2})
    return feat.values


class DNNClassifier(nn.Module):
    def __init__(self, in_features=8, num_classes=NUM_CLASSES):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.BatchNorm1d(64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, 32), nn.ReLU(),
            nn.Linear(32, num_classes),
        )

    def forward(self, x):
        return self.net(x)


def train_dnn(train_df, val_df, cw_tensor, device):
    X_tr = prepare_numeric(train_df)
    X_va = prepare_numeric(val_df)
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_va_s = scaler.transform(X_va)

    tr_dl = DataLoader(TensorDataset(torch.FloatTensor(X_tr_s), torch.LongTensor(train_df["label"].values)),
                       batch_size=64, shuffle=True, num_workers=NUM_WORKERS)
    va_dl = DataLoader(TensorDataset(torch.FloatTensor(X_va_s), torch.LongTensor(val_df["label"].values)),
                       batch_size=64, shuffle=False, num_workers=NUM_WORKERS)

    model = DNNClassifier().to(device)
    criterion = nn.CrossEntropyLoss(weight=cw_tensor)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    best_acc = 0.0

    for epoch in range(1, DNN_EPOCHS + 1):
        model.train()
        for x, y in tr_dl:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()

        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for x, y in va_dl:
                x, y = x.to(device), y.to(device)
                correct += model(x).argmax(1).eq(y).sum().item()
                total += y.size(0)
        acc = correct / total
        if acc > best_acc:
            best_acc = acc
            torch.save(model.state_dict(), MODEL_DIR / "best_dnn.pth")
        if epoch % 10 == 0 or epoch == 1:
            print(f"    DNN Epoch {epoch:2d}/{DNN_EPOCHS} | Val Acc: {acc:.4f}")

    model.load_state_dict(torch.load(MODEL_DIR / "best_dnn.pth", weights_only=True))
    print(f"    Best DNN Val Acc: {best_acc:.4f}")
    return model, scaler


# ============================================================
# 7-8. 비교 + 결과 저장
# ============================================================
def evaluate_and_save(lstm_model, vocab, bert_model, tokenizer,
                      dnn_model, scaler, test_df, df, label_names, short_names, device):
    y_test = test_df["label"].values

    # LSTM
    lstm_model.eval()
    test_ds = MaintenanceDataset(test_df["text"].tolist(), test_df["label"].tolist(), vocab)
    test_dl = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=NUM_WORKERS)
    lstm_preds = []
    with torch.no_grad():
        for x, _ in test_dl:
            lstm_preds.extend(lstm_model(x.to(device)).argmax(1).cpu().numpy())
    lstm_preds = np.array(lstm_preds)

    # BERT — 순수 PyTorch 예측 루프
    test_tok = BERTDataset(
        test_df["text"].tolist(), test_df["label"].tolist(), tokenizer)
    test_bert_dl = DataLoader(test_tok, batch_size=32, shuffle=False, num_workers=0)
    bert_model.eval()
    bert_preds = []
    with torch.no_grad():
        for batch in test_bert_dl:
            input_ids      = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            logits = bert_model(input_ids=input_ids,
                                attention_mask=attention_mask).logits
            bert_preds.extend(logits.argmax(dim=-1).cpu().numpy())
    bert_preds = np.array(bert_preds)

    # DNN
    X_test_s = scaler.transform(prepare_numeric(test_df))
    dnn_model.eval()
    with torch.no_grad():
        dnn_preds = dnn_model(torch.FloatTensor(X_test_s).to(device)).argmax(1).cpu().numpy()

    # 비교
    results = {}
    for name, preds in [("DNN (수치)", dnn_preds), ("LSTM (텍스트)", lstm_preds), ("BERT (텍스트)", bert_preds)]:
        results[name] = {
            "accuracy": accuracy_score(y_test, preds),
            "f1_macro": f1_score(y_test, preds, average="macro"),
            "f1_weighted": f1_score(y_test, preds, average="weighted"),
        }

    print(f'\n  {"모델":>18} | {"Accuracy":>9} | {"F1(macro)":>10} | {"F1(weighted)":>12}')
    print("  " + "-" * 56)
    for name, m in results.items():
        print(f'  {name:>18} | {m["accuracy"]:>8.4f} | {m["f1_macro"]:>9.4f} | {m["f1_weighted"]:>11.4f}')

    # 혼동행렬
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    for idx, (name, preds) in enumerate([("DNN", dnn_preds), ("LSTM", lstm_preds), ("BERT", bert_preds)]):
        cm = confusion_matrix(y_test, preds)
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes[idx],
                    xticklabels=short_names, yticklabels=short_names, cbar=False, annot_kws={"size": 9})
        axes[idx].set_xlabel("Predicted"); axes[idx].set_ylabel("Actual")
        axes[idx].set_title(name, fontweight="bold"); axes[idx].tick_params(labelsize=8)
    plt.suptitle("3모델 혼동행렬", fontsize=14)
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "04_confusion_matrices.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 비교 막대
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(results))
    w = 0.25
    model_names = list(results.keys())
    for i, (metric, label) in enumerate([("accuracy", "Accuracy"), ("f1_macro", "F1(macro)"), ("f1_weighted", "F1(weighted)")]):
        vals = [results[m][metric] for m in model_names]
        bars = ax.bar(x + i * w, vals, w, label=label)
        ax.bar_label(bars, fmt="%.3f", padding=2, fontsize=8)
    ax.set_xticks(x + w); ax.set_xticklabels(model_names)
    ax.set_ylim(0, 1.1); ax.set_title("모델 성능 비교"); ax.legend(); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "05_model_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 워드클라우드
    fail_types = [ft for ft in label_names if ft != "No Failure"]
    cols = 3; rows = (len(fail_types) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(15, 5 * rows))
    axes = axes.flatten()
    for idx, ft in enumerate(fail_types):
        texts = df[df["Failure Type"] == ft]["text"].tolist()
        wc = WordCloud(width=400, height=300, max_words=50, colormap="Reds",
                       background_color="white").generate(" ".join(texts))
        axes[idx].imshow(wc, interpolation="bilinear")
        axes[idx].set_title(ft, fontweight="bold"); axes[idx].axis("off")
    for i in range(len(fail_types), len(axes)):
        axes[i].axis("off")
    plt.suptitle("고장 유형별 워드클라우드", fontsize=14)
    plt.tight_layout()
    plt.savefig(RESULT_DIR / "06_wordclouds.png", dpi=150, bbox_inches="tight")
    plt.close()

    # JSON
    best_model_name = max(results, key=lambda m: results[m]["f1_macro"])
    summary = {
        "project": "소주제 D — 설비 고장 유형 예측",
        "dataset": "Machine Predictive Maintenance (10,000건)",
        "num_classes": NUM_CLASSES, "classes": label_names,
        "approach": "수치→텍스트 변환 후 NLP 모델 적용",
        "data_split": {"train": len(test_df) * 7 // 3, "val": len(test_df), "test": len(test_df)},
        "model_comparison": {n: {k: round(v, 4) for k, v in m.items()} for n, m in results.items()},
        "best_model": best_model_name, "seed": SEED,
    }
    with open(RESULT_DIR / "07_final_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n  {'=' * 56}")
    print("   소주제 D — 설비 고장 유형 예측 | 최종 결과")
    print(f"  {'=' * 56}")
    for name, m in results.items():
        marker = " ★" if name == best_model_name else ""
        print(f'  {name:>18} | {m["accuracy"]:>8.2%} | {m["f1_macro"]:>9.2%} | {m["f1_weighted"]:>11.2%}{marker}')
    print(f"\n  ★ 최고 모델: {best_model_name}")

    print(f"\n  저장된 파일:")
    for f in sorted(RESULT_DIR.glob("*")):
        print(f"    → results/{f.name}")


# ============================================================
# main
# ============================================================
def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(" 소주제 D. 설비 고장 유형 예측")
    print(" LSTM / BERT / DNN 비교 (수치→텍스트 변환)")
    print("=" * 60)

    print("\n[1/8] 환경 설정")
    device = setup_environment()

    print("\n[2/8] 데이터 로드 및 EDA")
    df = load_and_explore(device)

    print("\n[3/8] 피처 엔지니어링 + 텍스트 변환")
    df, train_df, val_df, test_df, label_names, short_names, cw_tensor = prepare_data(df, device)

    print("\n[4/8] LSTM 학습")
    lstm_model, vocab = train_lstm(train_df, val_df, cw_tensor, device)

    print("\n[5/8] BERT 학습")
    bert_model, tokenizer = train_bert(train_df, val_df, device)

    print("\n[6/8] DNN 학습")
    dnn_model, scaler = train_dnn(train_df, val_df, cw_tensor, device)

    print("\n[7/8] 3모델 비교")
    evaluate_and_save(lstm_model, vocab, bert_model, tokenizer,
                      dnn_model, scaler, test_df, df, label_names, short_names, device)

    print(f"\n{'=' * 60}")
    print(" 전체 파이프라인 완료!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
