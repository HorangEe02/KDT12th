"""
데이터 및 모델 로딩 유틸리티
- 인도네시아 로케일 CSV 파싱 (콤마=소수점, 마침표=천단위)
- 파생변수 생성
- 학습된 모델/스케일러/인코더 로딩
"""
import os
import json
import pandas as pd
import numpy as np
import joblib
import streamlit as st

# ── 경로 설정 ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DATA_PATH = os.path.join(
    PROJECT_DIR, "data",
    "Supply Chain Inventory Management Grocery Industry",
    "Inventory Management E-Grocery - InventoryData.csv"
)
MODELS_DIR = os.path.join(PROJECT_DIR, "outputs", "models")
FIGURES_DIR = os.path.join(PROJECT_DIR, "outputs", "figures")


# ── 인도네시아 로케일 숫자 변환 ────────────────────────────
def parse_id_number(val):
    """인도네시아 로케일 숫자 변환: '2.084,25' → 2084.25, '$5,81' → 5.81"""
    if pd.isna(val):
        return np.nan
    s = str(val).strip().replace("$", "").replace("%", "").strip()
    if s == "" or s == "-":
        return np.nan
    # 마침표=천단위, 콤마=소수점
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan


# ── 데이터 로딩 ────────────────────────────────────────────
@st.cache_data
def load_raw_data():
    """원본 CSV 로드 + 인도네시아 로케일 전처리 + 파생변수 생성"""
    df = pd.read_csv(DATA_PATH)

    # 날짜 변환
    for col in ["Received_Date", "Last_Purchase_Date", "Expiry_Date", "Audit_Date"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # 인도네시아 로케일 숫자 변환
    locale_cols = [
        "Avg_Daily_Sales", "Days_of_Inventory", "Unit_Cost_USD",
        "Last_Purchase_Price_USD", "Total_Inventory_Value_USD",
        "SKU_Churn_Rate", "Order_Frequency_per_month",
        "Supplier_OnTime_Pct", "Audit_Variance_Pct",
        "Demand_Forecast_Accuracy_Pct", "Forecast_Next_30d"
    ]
    for col in locale_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_id_number)

    # 파생변수 생성
    df["Days_To_Expiry"] = (df["Expiry_Date"] - df["Received_Date"]).dt.days
    df["Days_Since_Last_Order"] = (df["Received_Date"] - df["Last_Purchase_Date"]).dt.days
    df["Stock_Gap"] = df["Reorder_Point"] - df["Quantity_On_Hand"]
    df["Available_Stock"] = (
        df["Quantity_On_Hand"] - df["Quantity_Reserved"] - df["Quantity_Committed"]
    )
    df["Received_Month"] = df["Received_Date"].dt.month

    # Waste Risk 파생 (소주제 3 타겟)
    ads_safe = df["Avg_Daily_Sales"].replace(0, np.nan)
    df["Days_To_Deplete"] = df["Quantity_On_Hand"] / ads_safe
    reference_date = df["Received_Date"].max()
    df["Remaining_Shelf_Days"] = (df["Expiry_Date"] - reference_date).dt.days
    df["Waste_Risk"] = (df["Days_To_Deplete"] > df["Remaining_Shelf_Days"]).astype(int)
    df.loc[df["Days_To_Deplete"].isna(), "Waste_Risk"] = 0

    # FIFO/FEFO 인코딩
    df["FIFO_FEFO_encoded"] = (df["FIFO_FEFO"] == "FEFO").astype(int)

    # EOQ 관련 파생변수 (소주제 4)
    ordering_cost = 50
    holding_rate = 0.2
    annual_demand = df["Avg_Daily_Sales"] * 365
    holding_cost = df["Unit_Cost_USD"] * holding_rate
    holding_cost_safe = holding_cost.replace(0, np.nan)
    df["EOQ"] = np.sqrt(2 * annual_demand * ordering_cost / holding_cost_safe).fillna(0)

    cat_demand_cv = df.groupby("Category")["Avg_Daily_Sales"].transform(
        lambda x: x.std() / x.mean() if x.mean() > 0 else 0
    )
    df["Demand_Variability"] = cat_demand_cv

    df["Supply_Risk"] = df["Lead_Time_Days"] * (1 - df["Supplier_OnTime_Pct"] / 100)
    df["Reorder_Urgency"] = np.where(
        df["Safety_Stock"] > 0,
        (df["Quantity_On_Hand"] - df["Reorder_Point"]) / df["Safety_Stock"],
        0,
    )
    df["RP_SS_Ratio"] = np.where(
        df["Safety_Stock"] > 0,
        df["Reorder_Point"] / df["Safety_Stock"],
        0,
    )

    return df


# ── 모델 로딩 ──────────────────────────────────────────────
@st.cache_resource
def load_model(filename):
    """outputs/models/ 에서 pkl 파일 로드"""
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        # 서브폴더 탐색
        for sub in os.listdir(MODELS_DIR):
            sub_path = os.path.join(MODELS_DIR, sub, filename)
            if os.path.exists(sub_path):
                return joblib.load(sub_path)
        raise FileNotFoundError(f"Model not found: {filename}")
    return joblib.load(path)


@st.cache_data
def load_feature_info(filename):
    """feature_info JSON 로드"""
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        for sub in os.listdir(MODELS_DIR):
            sub_path = os.path.join(MODELS_DIR, sub, filename)
            if os.path.exists(sub_path):
                with open(sub_path, "r") as f:
                    return json.load(f)
        raise FileNotFoundError(f"Feature info not found: {filename}")
    with open(path, "r") as f:
        return json.load(f)


# ── 상수 ───────────────────────────────────────────────────
CATEGORIES = [
    "Bakery", "Beverages", "Dairy", "Fresh Produce", "Frozen",
    "Household", "Meat", "Pantry", "Personal Care", "Seafood"
]
ABC_CLASSES = ["A", "B", "C"]
WAREHOUSES = ["Jakarta", "Bandung", "Surabaya", "Denpasar", "Medan"]
PERISHABLE_CATEGORIES = ["Bakery", "Dairy", "Fresh Produce", "Meat", "Seafood"]
