"""
WMS 데이터 컬럼 설명, ML 알고리즘 소개, 용어 사전
"""

# ── 데이터 컬럼 설명 사전 ─────────────────────────────────────
COLUMN_DESC = {
    # 식별자
    "SKU_ID": {
        "name": "제품 ID",
        "desc": "각 제품(SKU)의 고유 식별 번호입니다.",
        "type": "식별자",
        "unit": "",
    },
    "SKU_Name": {
        "name": "제품명",
        "desc": "제품의 이름입니다.",
        "type": "텍스트",
        "unit": "",
    },
    # 범주형
    "Category": {
        "name": "카테고리",
        "desc": "제품이 속한 식품 분류입니다 (예: Dairy, Meat, Bakery, Fresh Produce 등).",
        "type": "범주형",
        "unit": "",
    },
    "ABC_Class": {
        "name": "ABC 등급",
        "desc": "매출 기여도에 따른 제품 중요도 등급입니다. A등급은 매출의 80%를 차지하는 핵심 제품, B등급은 15%, C등급은 5%입니다.",
        "type": "범주형",
        "unit": "",
    },
    "Inventory_Status": {
        "name": "재고 상태",
        "desc": "현재 재고의 상태를 나타냅니다. In Stock(충분), Low Stock(부족), Out of Stock(품절), Expiring Soon(유통기한 임박)으로 구분됩니다.",
        "type": "범주형",
        "unit": "",
    },
    "FIFO_FEFO": {
        "name": "출하 방식",
        "desc": "FIFO(First In First Out)는 먼저 입고된 제품을 먼저 출고, FEFO(First Expiry First Out)는 유통기한이 빠른 제품을 먼저 출고합니다.",
        "type": "범주형",
        "unit": "",
    },
    "Warehouse_Location": {
        "name": "창고 위치",
        "desc": "제품이 보관된 창고의 위치(도시)입니다.",
        "type": "범주형",
        "unit": "",
    },
    "Supplier_Name": {
        "name": "공급업체명",
        "desc": "제품을 공급하는 업체의 이름입니다.",
        "type": "텍스트",
        "unit": "",
    },
    # 수치형 — 수량
    "Quantity_On_Hand": {
        "name": "현재 보유 수량",
        "desc": "창고에 현재 보관 중인 제품의 총 수량입니다. 많을수록 재고가 넉넉합니다.",
        "type": "수치형",
        "unit": "개",
    },
    "Quantity_Reserved": {
        "name": "예약 수량",
        "desc": "이미 주문이 들어와서 출하 대기 중인 수량입니다.",
        "type": "수치형",
        "unit": "개",
    },
    "Quantity_Committed": {
        "name": "확약 수량",
        "desc": "특정 주문에 배정되어 다른 용도로 사용할 수 없는 수량입니다.",
        "type": "수치형",
        "unit": "개",
    },
    "Damaged_Qty": {
        "name": "손상 수량",
        "desc": "파손되거나 손상되어 판매할 수 없는 수량입니다.",
        "type": "수치형",
        "unit": "개",
    },
    "Returns_Qty": {
        "name": "반품 수량",
        "desc": "고객이 반품한 수량입니다.",
        "type": "수치형",
        "unit": "개",
    },
    "Safety_Stock": {
        "name": "안전 재고",
        "desc": "예상치 못한 수요 증가나 납품 지연에 대비해 항상 유지해야 하는 최소 재고량입니다.",
        "type": "수치형",
        "unit": "개",
    },
    "Reorder_Point": {
        "name": "재주문점 (ROP)",
        "desc": "재고가 이 수량 아래로 떨어지면 새로운 주문을 넣어야 하는 기준선입니다.",
        "type": "수치형",
        "unit": "개",
    },
    "Available_Stock": {
        "name": "가용 재고",
        "desc": "실제로 사용 가능한 재고량입니다 (보유 수량 - 예약 - 확약).",
        "type": "수치형(파생)",
        "unit": "개",
    },
    "Stock_Gap": {
        "name": "재고 갭",
        "desc": "재주문점 대비 부족한 수량입니다. 양수면 재고 부족, 음수면 여유 있음을 의미합니다.",
        "type": "수치형(파생)",
        "unit": "개",
    },
    # 수치형 — 판매/수요
    "Avg_Daily_Sales": {
        "name": "일평균 판매량",
        "desc": "하루에 평균적으로 판매되는 수량입니다. 이 값이 클수록 빠르게 팔리는 인기 제품입니다.",
        "type": "수치형",
        "unit": "개/일",
    },
    "Forecast_Next_30d": {
        "name": "30일 수요 예측",
        "desc": "향후 30일간 예상되는 판매 수량입니다.",
        "type": "수치형",
        "unit": "개",
    },
    "Annual_Demand": {
        "name": "연간 수요",
        "desc": "1년간 예상되는 총 판매량입니다 (일평균 판매량 x 365).",
        "type": "수치형(파생)",
        "unit": "개/년",
    },
    # 수치형 — 기간
    "Days_of_Inventory": {
        "name": "재고 소진 예상일",
        "desc": "현재 재고가 몇 일 동안 유지될 수 있는지를 나타냅니다. 낮을수록 곧 재고가 바닥남을 의미합니다.",
        "type": "수치형",
        "unit": "일",
    },
    "Lead_Time_Days": {
        "name": "배송 소요일",
        "desc": "주문 후 물건이 창고에 도착하기까지 걸리는 날수입니다.",
        "type": "수치형",
        "unit": "일",
    },
    "Days_To_Expiry": {
        "name": "유통기한 잔여일",
        "desc": "유통기한까지 남은 날수입니다. 적을수록 폐기 위험이 높습니다.",
        "type": "수치형(파생)",
        "unit": "일",
    },
    "Stock_Age_Days": {
        "name": "재고 보관일",
        "desc": "현재 재고가 창고에 보관된 기간입니다.",
        "type": "수치형",
        "unit": "일",
    },
    "Days_Since_Last_Order": {
        "name": "최근 주문 이후 경과일",
        "desc": "마지막으로 주문을 넣은 이후 경과한 날수입니다.",
        "type": "수치형(파생)",
        "unit": "일",
    },
    "Days_To_Deplete": {
        "name": "재고 소진 예상일(계산)",
        "desc": "현재 판매 속도로 재고가 모두 소진될 때까지 예상 일수입니다.",
        "type": "수치형(파생)",
        "unit": "일",
    },
    "Remaining_Shelf_Days": {
        "name": "남은 유통기한",
        "desc": "기준일로부터 유통기한까지 남은 날수입니다.",
        "type": "수치형(파생)",
        "unit": "일",
    },
    # 수치형 — 금액
    "Unit_Cost_USD": {
        "name": "단가",
        "desc": "제품 1개당 원가(구매 비용)입니다.",
        "type": "수치형",
        "unit": "$",
    },
    "Last_Purchase_Price_USD": {
        "name": "최근 구매 단가",
        "desc": "가장 최근에 이 제품을 구매했을 때의 단가입니다.",
        "type": "수치형",
        "unit": "$",
    },
    "Total_Inventory_Value_USD": {
        "name": "총 재고 금액",
        "desc": "현재 보유 재고의 총 금액입니다 (수량 x 단가).",
        "type": "수치형",
        "unit": "$",
    },
    # 수치형 — 비율/지표
    "SKU_Churn_Rate": {
        "name": "제품 이탈률",
        "desc": "제품이 카탈로그에서 제외될 확률입니다. 높을수록 판매가 저조한 제품입니다.",
        "type": "수치형",
        "unit": "%",
    },
    "Order_Frequency_per_month": {
        "name": "월간 주문 빈도",
        "desc": "한 달에 이 제품의 주문이 몇 번 발생하는지 나타냅니다.",
        "type": "수치형",
        "unit": "회/월",
    },
    "Supplier_OnTime_Pct": {
        "name": "공급업체 정시 납품률",
        "desc": "공급업체가 약속한 날짜에 제때 납품하는 비율입니다. 100%에 가까울수록 신뢰할 수 있는 업체입니다.",
        "type": "수치형",
        "unit": "%",
    },
    "Demand_Forecast_Accuracy_Pct": {
        "name": "수요 예측 정확도",
        "desc": "과거 수요 예측이 실제와 얼마나 일치했는지의 비율입니다.",
        "type": "수치형",
        "unit": "%",
    },
    "Audit_Variance_Pct": {
        "name": "실사 오차율",
        "desc": "재고 실사(확인) 시 시스템 기록과 실제 수량의 차이 비율입니다.",
        "type": "수치형",
        "unit": "%",
    },
    "Count_Variance": {
        "name": "수량 오차",
        "desc": "시스템에 기록된 수량과 실제 수량의 차이입니다.",
        "type": "수치형",
        "unit": "개",
    },
    # 수치형 — EOQ/발주 관련
    "EOQ": {
        "name": "경제적 주문량 (EOQ)",
        "desc": "총 비용(주문비용 + 보관비용)을 최소화하는 1회 최적 주문 수량입니다.",
        "type": "수치형(파생)",
        "unit": "개",
    },
    "Holding_Cost": {
        "name": "보관 비용",
        "desc": "제품 1개를 1년간 보관하는 데 드는 비용입니다 (단가 x 보관비율).",
        "type": "수치형(파생)",
        "unit": "$/년",
    },
    "Demand_Variability": {
        "name": "수요 변동성",
        "desc": "카테고리 내 수요의 변동 계수입니다. 높을수록 수요 예측이 어렵습니다.",
        "type": "수치형(파생)",
        "unit": "",
    },
    "Supply_Risk": {
        "name": "공급 위험도",
        "desc": "납품 지연 위험을 나타내는 지표입니다 (배송일 x 지연 확률).",
        "type": "수치형(파생)",
        "unit": "",
    },
    "Reorder_Urgency": {
        "name": "발주 긴급도",
        "desc": "재주문이 얼마나 급한지를 나타냅니다. 음수이면 재고가 재주문점 아래로 떨어진 상태입니다.",
        "type": "수치형(파생)",
        "unit": "",
    },
    "RP_SS_Ratio": {
        "name": "ROP/안전재고 비율",
        "desc": "재주문점 대비 안전재고의 비율입니다.",
        "type": "수치형(파생)",
        "unit": "",
    },
    # 위험 관련
    "Waste_Risk": {
        "name": "폐기 위험 여부",
        "desc": "유통기한 내에 재고를 소진하지 못할 위험이 있는지 여부입니다 (1=위험, 0=안전).",
        "type": "이진(파생)",
        "unit": "",
    },
    "Risk_Pred": {
        "name": "AI 폐기 위험 예측",
        "desc": "머신러닝 모델이 예측한 폐기 위험 여부입니다.",
        "type": "이진(예측)",
        "unit": "",
    },
    "Risk_Prob": {
        "name": "폐기 위험 확률",
        "desc": "AI가 예측한 폐기될 확률입니다. 0~1 사이 값이며 1에 가까울수록 위험합니다.",
        "type": "수치형(예측)",
        "unit": "",
    },
    # 클러스터
    "Cluster": {
        "name": "제품 그룹",
        "desc": "AI가 유사한 특성을 가진 제품끼리 분류한 그룹 번호입니다.",
        "type": "범주형(예측)",
        "unit": "",
    },
    "Cluster_Name": {
        "name": "제품 그룹명",
        "desc": "AI가 분류한 제품 그룹의 이름입니다 (빠른 회전, 느린 회전 등).",
        "type": "범주형(예측)",
        "unit": "",
    },
    "Dynamic_ROP": {
        "name": "동적 재주문점",
        "desc": "일평균 판매량과 배송 소요일을 고려하여 동적으로 계산한 재주문점입니다.",
        "type": "수치형(파생)",
        "unit": "개",
    },
    "Stock_Coverage_Days": {
        "name": "재고 커버리지",
        "desc": "안전재고를 제외한 초과 재고가 며칠분인지 나타냅니다.",
        "type": "수치형(파생)",
        "unit": "일",
    },
}

# 분석 가능한 수치형 컬럼 (통계분석 대상)
NUMERIC_ANALYSIS_COLS = [
    "Quantity_On_Hand", "Avg_Daily_Sales", "Days_of_Inventory",
    "Lead_Time_Days", "Unit_Cost_USD", "Total_Inventory_Value_USD",
    "Safety_Stock", "Reorder_Point", "Forecast_Next_30d",
    "Days_To_Expiry", "EOQ", "Order_Frequency_per_month",
    "Supplier_OnTime_Pct", "SKU_Churn_Rate",
    "Damaged_Qty", "Returns_Qty", "Stock_Age_Days",
]

# 범주형 컬럼 (필터/그룹핑 대상)
CATEGORICAL_COLS = [
    "Category", "ABC_Class", "Inventory_Status", "FIFO_FEFO",
    "Warehouse_Location", "Supplier_Name",
]


# ── ML 알고리즘 소개 사전 ─────────────────────────────────────
ALGORITHM_INFO = {
    "LightGBM_Classification": {
        "name": "LightGBM (분류 모델)",
        "icon": "tree",
        "summary": "마이크로소프트가 개발한 고성능 그래디언트 부스팅 알고리즘",
        "how_it_works": (
            "LightGBM은 **수백 개의 작은 결정 트리(Decision Tree)**를 순차적으로 만들어, "
            "이전 트리가 틀린 부분을 다음 트리가 보완하는 방식으로 학습합니다.\n\n"
            "- **Leaf-wise 성장**: 가장 효과적인 잎(Leaf)을 우선 분할하여 빠르고 정확합니다.\n"
            "- **히스토그램 기반**: 연속 값을 구간으로 나눠 계산 속도를 크게 높입니다.\n"
            "- **범주형 직접 처리**: 카테고리 데이터를 별도 인코딩 없이 바로 학습합니다."
        ),
        "strengths": "대용량 데이터에서 빠른 학습 속도와 높은 정확도를 자랑하며, 과적합(Overfitting)에 강합니다.",
        "use_case": "재고 상태(In Stock / Low Stock / Out of Stock / Expiring Soon)를 예측합니다.",
        "metrics_explained": {
            "정확도 (Accuracy)": "전체 예측 중 맞춘 비율. 98.8%면 1000개 중 988개를 정확히 분류한 것입니다.",
            "혼동 행렬 (Confusion Matrix)": "실제 상태 vs 예측 상태를 표로 비교한 것. 대각선 값이 높을수록 좋습니다.",
            "정밀도 (Precision)": "특정 상태로 예측한 것 중 실제로 맞은 비율.",
            "재현율 (Recall)": "실제 특정 상태인 것 중 모델이 잡아낸 비율.",
        },
    },
    "XGBoost_Regression": {
        "name": "XGBoost (회귀 모델)",
        "icon": "chart",
        "summary": "Kaggle 대회에서 가장 많이 우승한 그래디언트 부스팅 알고리즘",
        "how_it_works": (
            "XGBoost도 **여러 결정 트리를 순차적으로 조합**하는 앙상블 기법입니다.\n\n"
            "- **정규화(Regularization)**: L1/L2 정규화로 과적합을 방지합니다.\n"
            "- **결측치 자동 처리**: 빠진 데이터를 자동으로 최적 방향에 배치합니다.\n"
            "- **트리 가지치기**: 불필요한 분기를 자동으로 제거하여 효율적입니다."
        ),
        "strengths": "높은 예측 정확도와 강력한 정규화, 빠른 학습 속도를 제공합니다.",
        "use_case": "제품의 일평균 판매량(Avg_Daily_Sales)을 예측합니다.",
        "metrics_explained": {
            "R² (결정계수)": "모델이 데이터의 변동을 얼마나 설명하는지. 1에 가까울수록 좋고, 0.948이면 94.8%의 변동을 설명합니다.",
            "RMSE (평균제곱근오차)": "예측 오차의 크기. 작을수록 예측이 정확합니다. 단위는 원래 데이터와 동일합니다.",
            "MAE (평균절대오차)": "예측값과 실제값 차이의 평균. 해석이 직관적입니다.",
            "Bias (편향)": "양수면 과대예측, 음수면 과소예측 경향입니다.",
        },
    },
    "Risk_Classification": {
        "name": "폐기 위험 탐지 모델",
        "icon": "warning",
        "summary": "유통기한과 판매 속도를 기반으로 폐기 위험을 탐지하는 이진 분류 모델",
        "how_it_works": (
            "이 모델은 제품의 다양한 특성을 입력받아 **폐기될 가능성(0~100%)**을 출력합니다.\n\n"
            "- **입력 특성**: 유통기한, 판매 속도, 보유 수량, 카테고리, 출하 방식 등\n"
            "- **학습 방법**: 과거에 실제로 폐기된 제품들의 패턴을 학습합니다.\n"
            "- **위험 기준**: 현재 판매 속도로 유통기한 내에 소진이 불가능하면 '위험'으로 판정합니다."
        ),
        "strengths": "98.8%의 높은 정확도로 폐기 위험 제품을 사전에 탐지할 수 있습니다.",
        "use_case": "각 제품의 폐기 위험 여부(위험/안전)를 예측합니다.",
        "metrics_explained": {
            "정확도 (Accuracy)": "전체 예측 중 맞춘 비율입니다.",
            "AUC-ROC": "위험/안전을 얼마나 잘 구분하는지. 1에 가까울수록 좋습니다.",
            "위험 확률": "0~1 사이 값. 0.7 이상이면 즉시 조치, 0.3~0.7은 주의, 0.3 미만은 안전입니다.",
        },
    },
    "KMeans_Clustering": {
        "name": "K-Means 군집화",
        "icon": "cluster",
        "summary": "유사한 제품끼리 자동으로 그룹화하는 비지도 학습 알고리즘",
        "how_it_works": (
            "K-Means는 **미리 지정한 K개의 중심점(Centroid)**을 기준으로 가장 가까운 데이터끼리 묶는 알고리즘입니다.\n\n"
            "1. K개의 중심점을 무작위로 배치합니다.\n"
            "2. 각 데이터를 가장 가까운 중심점에 배정합니다.\n"
            "3. 각 그룹의 평균 위치로 중심점을 이동합니다.\n"
            "4. 2~3단계를 변화가 없을 때까지 반복합니다."
        ),
        "strengths": "직관적이고 빠르며, 대규모 데이터에서도 효율적입니다.",
        "use_case": "제품을 유사한 특성별로 그룹화하여 그룹별 맞춤 발주 전략을 수립합니다.",
        "metrics_explained": {
            "실루엣 점수 (Silhouette)": "같은 그룹 내 유사도 vs 다른 그룹과의 차이. -1~1 사이이며 1에 가까울수록 그룹이 잘 나뉘었습니다.",
            "관성 (Inertia)": "각 데이터와 중심점 사이 거리의 합. 작을수록 밀집된 군집입니다.",
        },
    },
    "DBSCAN": {
        "name": "DBSCAN (밀도 기반 군집화)",
        "icon": "cluster",
        "summary": "밀도가 높은 지역을 자동으로 찾아 군집을 형성하는 알고리즘",
        "how_it_works": (
            "DBSCAN은 **K-Means와 달리 군집 수를 미리 정하지 않아도** 되는 알고리즘입니다.\n\n"
            "- **핵심점(Core Point)**: 주변에 일정 수 이상의 데이터가 있는 점\n"
            "- **경계점(Border Point)**: 핵심점 근처에 있지만 자체 밀도는 낮은 점\n"
            "- **이상치(Noise)**: 어떤 군집에도 속하지 않는 고립된 점\n\n"
            "밀집된 영역을 따라가며 자연스러운 형태의 군집을 발견합니다."
        ),
        "strengths": "비정형 형태의 군집 발견, 이상치 자동 탐지, 군집 수 자동 결정이 가능합니다.",
        "use_case": "일반적인 패턴에서 벗어난 특이한 제품(이상치)을 발견합니다.",
        "metrics_explained": {
            "eps (이웃 반경)": "한 점 주변으로 이웃을 찾는 반경. 너무 크면 군집이 합쳐지고, 너무 작으면 이상치가 많아집니다.",
            "min_samples (최소 이웃 수)": "핵심점이 되기 위한 최소 이웃 데이터 수입니다.",
            "이상치 비율": "전체 데이터 중 어떤 군집에도 속하지 않는 데이터의 비율입니다.",
        },
    },
    "GMM": {
        "name": "GMM (가우시안 혼합 모델)",
        "icon": "cluster",
        "summary": "데이터가 여러 개의 정규분포(가우시안)로 구성되어 있다고 가정하는 확률적 군집화",
        "how_it_works": (
            "GMM은 각 군집이 **정규분포(종 모양 곡선)**를 따른다고 가정합니다.\n\n"
            "- 각 군집의 평균, 분산, 크기를 추정합니다.\n"
            "- 각 데이터가 각 군집에 속할 **확률**을 계산합니다.\n"
            "- K-Means처럼 딱 하나의 군집에 배정하지 않고, '이 제품은 A그룹 70%, B그룹 30%' 같이 소속 확률을 제공합니다."
        ),
        "strengths": "군집 소속의 불확실성을 확률로 표현하여 더 유연한 분류가 가능합니다.",
        "use_case": "제품 그룹의 경계가 모호한 경우 확률적으로 분류합니다.",
        "metrics_explained": {
            "BIC (베이즈 정보 기준)": "모델의 적합도. 작을수록 좋은 모델입니다.",
            "AIC (아카이케 정보 기준)": "모델의 복잡도와 적합도의 균형. 작을수록 좋습니다.",
            "소속 확률": "각 데이터가 각 군집에 속할 확률. 높은 확률의 군집으로 배정됩니다.",
        },
    },
}


# ── 비전공자용 용어 사전 ──────────────────────────────────────
GLOSSARY = {
    "머신러닝 (Machine Learning)": "컴퓨터가 데이터에서 패턴을 스스로 학습하여 예측이나 분류를 수행하는 인공지능 기술입니다.",
    "지도 학습 (Supervised Learning)": "정답(라벨)이 있는 데이터로 학습합니다. 예: '이 제품은 품절이다' 같은 정답을 알려주고 학습시킵니다.",
    "비지도 학습 (Unsupervised Learning)": "정답 없이 데이터의 패턴만으로 학습합니다. 예: 비슷한 제품끼리 자동으로 그룹을 만듭니다.",
    "피처 (Feature)": "모델이 예측에 사용하는 입력 데이터의 각 항목입니다. 예: 보유 수량, 판매량, 유통기한 등.",
    "타겟 (Target)": "모델이 예측하려는 값입니다. 예: 재고 상태, 판매량, 폐기 위험 등.",
    "훈련 (Training)": "모델이 과거 데이터에서 패턴을 학습하는 과정입니다.",
    "예측 (Prediction)": "학습된 모델이 새로운 데이터에 대해 결과를 출력하는 것입니다.",
    "과적합 (Overfitting)": "모델이 학습 데이터에만 너무 맞춰져서 새로운 데이터에서 성능이 떨어지는 현상입니다.",
    "앙상블 (Ensemble)": "여러 모델을 조합하여 하나보다 더 좋은 성능을 내는 기법입니다.",
    "그래디언트 부스팅": "이전 모델의 오류를 다음 모델이 보정하는 방식으로 순차적으로 성능을 개선하는 앙상블 기법입니다.",
    "스케일링 (Scaling)": "데이터의 크기(범위)를 비슷하게 맞추는 전처리. 예: 수량(0~1000)과 비율(0~100)의 스케일을 통일합니다.",
    "혼동 행렬 (Confusion Matrix)": "분류 모델의 성능을 시각화한 표. 행=실제값, 열=예측값이며 대각선이 정답입니다.",
    "정밀도 (Precision)": "'A라고 예측한 것 중 실제 A인 비율'. 거짓 양성(False Positive)을 줄이고 싶을 때 중요합니다.",
    "재현율 (Recall)": "'실제 A인 것 중 A라고 잡아낸 비율'. 놓치면 안 되는 경우(위험 탐지)에 중요합니다.",
    "R² (결정계수)": "모델이 데이터의 변동을 얼마나 잘 설명하는지 0~1 사이로 표현합니다.",
    "RMSE (평균제곱근오차)": "예측 오차의 대표값. 이상치(큰 오차)에 민감합니다.",
    "MAE (평균절대오차)": "예측 오차의 평균 크기. 해석이 직관적입니다.",
    "SHAP (SHapley Additive exPlanations)": "각 피처가 예측에 얼마나 기여했는지를 수학적으로 계산하는 설명 기법입니다.",
    "피처 중요도 (Feature Importance)": "모델이 예측할 때 어떤 입력 데이터를 가장 많이 참고했는지 순위를 매긴 것입니다.",
    "EOQ (경제적 주문량)": "주문 비용과 보관 비용의 합이 최소가 되는 1회 주문 수량입니다.",
    "안전 재고 (Safety Stock)": "수요 변동이나 납품 지연에 대비해 추가로 보관하는 여유 재고입니다.",
    "재주문점 (Reorder Point)": "재고가 이 수준 이하로 떨어지면 새로 주문해야 하는 기준선입니다.",
    "군집화 (Clustering)": "비슷한 특성을 가진 데이터끼리 자동으로 그룹화하는 비지도 학습 기법입니다.",
}


def render_glossary(st_module):
    """비전공자용 용어 사전을 expander로 렌더링"""
    with st_module.expander("용어 사전 (비전공자를 위한 개념 설명)", expanded=False):
        for term, definition in GLOSSARY.items():
            st_module.markdown(f"**{term}**")
            st_module.caption(definition)


def render_algorithm_info(st_module, algo_key):
    """ML 알고리즘 소개 섹션을 렌더링"""
    info = ALGORITHM_INFO.get(algo_key)
    if not info:
        return

    st_module.markdown(f"### {info['name']}")
    st_module.info(f"**{info['summary']}**")

    with st_module.expander("알고리즘 작동 원리", expanded=False):
        st_module.markdown(info["how_it_works"])
        st_module.success(f"**장점**: {info['strengths']}")
        st_module.markdown(f"**이 페이지에서의 역할**: {info['use_case']}")

    with st_module.expander("성능 지표 해석 가이드", expanded=False):
        for metric, explanation in info["metrics_explained"].items():
            st_module.markdown(f"- **{metric}**: {explanation}")


def render_feature_importance(st_module, model, feature_names, title="피처 중요도 분석"):
    """모델의 피처 중요도를 바 차트로 렌더링"""
    import plotly.express as px
    import pandas as pd

    importances = None

    # tree 기반 모델의 feature_importances_
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        import numpy as np
        importances = np.abs(model.coef_).flatten()
        if len(importances) != len(feature_names):
            # multiclass일 경우 평균
            if hasattr(model, "coef_") and model.coef_.ndim > 1:
                importances = np.abs(model.coef_).mean(axis=0)

    if importances is None or len(importances) != len(feature_names):
        st_module.warning("이 모델은 피처 중요도를 지원하지 않습니다.")
        return

    fi_df = pd.DataFrame({
        "피처": feature_names,
        "중요도": importances,
    }).sort_values("중요도", ascending=True).tail(15)

    # 피처명을 한글로 변환
    fi_df["피처명"] = fi_df["피처"].map(
        lambda x: COLUMN_DESC.get(x, {}).get("name", x)
    )

    fig = px.bar(fi_df, x="중요도", y="피처명", orientation="h",
                 color="중요도", color_continuous_scale="Viridis",
                 title=title)
    fig.update_layout(height=max(350, len(fi_df) * 28), margin=dict(l=10, r=10, t=40, b=10),
                      yaxis_title="", xaxis_title="중요도 점수",
                      coloraxis_showscale=False)
    st_module.plotly_chart(fig, use_container_width=True)

    # 상위 3개 피처 해석
    top3 = fi_df.tail(3).iloc[::-1]
    st_module.markdown("**상위 3 핵심 피처 해석:**")
    for i, (_, row) in enumerate(top3.iterrows(), 1):
        col_info = COLUMN_DESC.get(row["피처"], {})
        desc = col_info.get("desc", "")
        st_module.markdown(f"{i}. **{row['피처명']}** (중요도: {row['중요도']:.4f})")
        if desc:
            st_module.caption(f"   {desc}")


def render_shap_analysis(st_module, model, X_scaled, feature_names, max_display=15):
    """SHAP 분석을 수행하고 시각화 (설치되어 있을 경우)"""
    try:
        import shap
        import matplotlib.pyplot as plt
        import numpy as np

        st_module.markdown("#### SHAP 분석 (모델 예측 기여도)")
        st_module.caption("각 피처가 개별 예측에 얼마나 기여했는지를 보여줍니다. "
                         "빨간색은 예측값을 높이는 방향, 파란색은 낮추는 방향입니다.")

        # 샘플링 (속도 위해)
        sample_size = min(100, len(X_scaled))
        X_sample = X_scaled.iloc[:sample_size] if hasattr(X_scaled, 'iloc') else X_scaled[:sample_size]

        # Explainer 선택
        if hasattr(model, "feature_importances_"):
            explainer = shap.TreeExplainer(model)
        else:
            explainer = shap.LinearExplainer(model, X_sample)

        shap_values = explainer.shap_values(X_sample)

        # multiclass인 경우 평균
        if isinstance(shap_values, list):
            shap_values = np.abs(np.array(shap_values)).mean(axis=0)

        # 한글 피처명
        kr_names = [COLUMN_DESC.get(f, {}).get("name", f) for f in feature_names]

        # summary plot
        fig, ax = plt.subplots(figsize=(10, max(5, min(max_display, len(feature_names)) * 0.4)))
        if hasattr(X_sample, 'values'):
            X_for_plot = X_sample.copy()
            X_for_plot.columns = kr_names
        else:
            import pandas as pd
            X_for_plot = pd.DataFrame(X_sample, columns=kr_names)

        shap.summary_plot(shap_values, X_for_plot, max_display=max_display,
                         show=False, plot_size=None)
        plt.tight_layout()
        st_module.pyplot(fig)
        plt.close(fig)

        return True
    except ImportError:
        st_module.info("SHAP 라이브러리가 설치되지 않았습니다. `pip install shap`으로 설치하면 더 자세한 분석을 볼 수 있습니다.")
        return False
    except Exception as e:
        st_module.warning(f"SHAP 분석 중 오류가 발생했습니다: {str(e)[:100]}")
        return False
