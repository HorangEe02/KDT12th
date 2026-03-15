"""
모델 추론을 위한 전처리 파이프라인
- 각 소주제별 피처 준비 함수
- 스케일링 + 인코딩 적용
"""
import pandas as pd
import numpy as np


def prepare_classification_features(df, feature_info):
    """소주제 1: 재고 상태 분류용 피처 준비"""
    feature_names = feature_info["all_features_after_encoding"]

    num_cols = feature_info["num_features"]
    X = df[num_cols].copy()

    # One-Hot: Category (drop_first=True → Bakery 제거)
    for cat in [
        "Beverages", "Dairy", "Fresh Produce", "Frozen",
        "Household", "Meat", "Pantry", "Personal Care", "Seafood"
    ]:
        X[f"Category_{cat}"] = (df["Category"] == cat).astype(int)

    # One-Hot: ABC_Class (drop_first=True → A 제거)
    X["ABC_Class_B"] = (df["ABC_Class"] == "B").astype(int)
    X["ABC_Class_C"] = (df["ABC_Class"] == "C").astype(int)

    return X[feature_names]


def prepare_regression_features(df, feature_info):
    """소주제 2: 판매량 예측용 피처 준비"""
    feature_names = feature_info["feature_names"]
    num_cols = feature_info["num_features"]

    X = df[num_cols].copy()

    for cat in [
        "Beverages", "Dairy", "Fresh Produce", "Frozen",
        "Household", "Meat", "Pantry", "Personal Care", "Seafood"
    ]:
        X[f"Category_{cat}"] = (df["Category"] == cat).astype(int)

    X["ABC_Class_B"] = (df["ABC_Class"] == "B").astype(int)
    X["ABC_Class_C"] = (df["ABC_Class"] == "C").astype(int)

    return X[feature_names]


def prepare_risk_features(df, feature_info):
    """소주제 3: 폐기 위험 예측용 피처 준비"""
    feature_names = feature_info["feature_names"]
    num_cols = feature_info["numeric_features"]

    X = df[num_cols].copy()

    # Category One-Hot (Cat_ prefix, drop Bakery)
    for cat in [
        "Beverages", "Dairy", "Fresh Produce", "Frozen",
        "Household", "Meat", "Pantry", "Personal Care", "Seafood"
    ]:
        X[f"Cat_{cat}"] = (df["Category"] == cat).astype(int)

    X["ABC_B"] = (df["ABC_Class"] == "B").astype(int)
    X["ABC_C"] = (df["ABC_Class"] == "C").astype(int)
    X["FIFO_FEFO_encoded"] = df["FIFO_FEFO_encoded"]

    return X[feature_names]


def prepare_doi_features(df, feature_info):
    """소주제 4 Phase A: DOI 예측용 피처 준비"""
    features = feature_info["phase_a"]["features"]

    num_cols = [
        "Unit_Cost_USD", "Reorder_Point", "Safety_Stock",
        "Lead_Time_Days", "Order_Frequency_per_month", "Supplier_OnTime_Pct"
    ]
    X = df[num_cols].copy()

    for cat in [
        "Beverages", "Dairy", "Fresh Produce", "Frozen",
        "Household", "Meat", "Pantry", "Personal Care", "Seafood"
    ]:
        X[f"Category_{cat}"] = (df["Category"] == cat).astype(int)

    X["ABC_B"] = (df["ABC_Class"] == "B").astype(int)
    X["ABC_C"] = (df["ABC_Class"] == "C").astype(int)

    return X[features]


def prepare_cluster_features(df, feature_names):
    """소주제 4 Phase B: 클러스터링용 피처 준비"""
    return df[feature_names].copy()
