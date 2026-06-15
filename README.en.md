[한국어](./README.md) | **English**

# Junyeong Park · Data Scientist Portfolio

> **Statistics B.S. + 13 hands-on AI/Big Data projects**
>
> After graduating in Statistics from Keimyung University, I completed the **K-Digital Training Cohort 12 — AI/Big Data Specialist Program**
> (hosted by Kyungpook National University & Korea's Ministry of Employment and Labor, 2025.12–2026.06),
> implementing the full data lifecycle — statistical analysis → machine learning → deep learning → computer vision → NLP → full-stack AI services —
> across **13 mini-projects**.
> My strength: framing problems with statistical reasoning, modeling them with ML/DL, and shipping them as services to validate value.

<br>

| | |
|------|------|
| **Name** | Junyeong Park (박준영) |
| **Major** | B.S. in Statistics, Keimyung University |
| **Program** | K-Digital Training Cohort 12 · AI/Big Data Specialist (Kyungpook Nat'l Univ. · Ministry of Employment and Labor) |
| **Period** | 2025.12 – 2026.06 |
| **GitHub** | [github.com/HorangEe02](https://github.com/HorangEe02) |
| **Portfolio** | [Notion Portfolio](https://www.notion.so/31879104c6f38039a53cfaa4b64ef712) |

---

## 🎯 Strengths at a Glance

- **Statistical rigor** — hypothesis testing, confounder control, and multivariate regression to separate correlation from causation (major-based)
- **End-to-end modeling** — selecting and combining classification, regression, unsupervised learning, deep learning, and NLP to fit the data
- **Insight → decision** — interpreting models with SHAP / feature importance and connecting them to business actions
- **Productization** — shipping models as real, working products with Streamlit, FastAPI, and Next.js
- **Team leadership** — team lead on 2 projects (Phase 8 & 9): topic planning, role allocation, and integration

---

## 🧰 Tech Stack (mapped to evidence projects)

| Area | Technologies | Featured in |
|------|------|--------------|
| **Languages · Foundations** | Python, SQL, Git, OOP | Phase 1 · all phases |
| **Statistics · Analysis** | Pandas, NumPy, statsmodels, logistic regression, chi-square·ANOVA·t-test, effect size | Phase 2 · 5 · 7 |
| **Visualization** | Matplotlib, Seaborn, Plotly, Streamlit | Phase 5 · 8 · 9 · 10 |
| **Data collection** | Selenium, BeautifulSoup, public APIs | Phase 4 · 6 · 12 · 13&14 |
| **Machine learning** | Scikit-learn, XGBoost, LightGBM, K-Means, SHAP | Phase 2 · 8 · 9 |
| **Deep learning · CV** | PyTorch, CNN, ResNet, U-Net, YOLOv8, Autoencoder, OpenCV | Phase 9 · 10 |
| **NLP · LLM** | HuggingFace Transformers, KcELECTRA, BERT, NER, sentiment analysis, RAG (ChromaDB), Ollama, Gemini, Tool Calling | Phase 6 · 10 · 11 · 13&14 |
| **Web · Deploy · Infra** | FastAPI, Next.js 16, React, Docker Compose, Firebase, Cloudflare Tunnel | Phase 11 · 12 · 13&14 |

---

## ⭐ Featured Projects

> The **top 5** of 13 that best demonstrate data-science capability.
> See the full list under [📚 All Projects](#-all-projects-13).

### 1. Integrated Lunch-Recommendation AI Dashboard — *Phase 13 & 14* 🏆

> **A capstone-scale full-stack AI service that solves "what should I eat today?" with data — integrating the entire KDT curriculum**

| | |
|------|------|
| **Problem** | Office workers' recurring lunch decision fatigue, biased eating patterns, weekly nutritional imbalance |
| **Approach** | A single pipeline unifying 4 axes — weather, nutrition, team preference, restaurant info — plus weighted-score recommendation + 7 NLP modules |
| **NLP** | KcELECTRA sentiment · menu normalization · RAG chatbot (ChromaDB) · ABSA · Food NER · multi-turn Tool Calling · NLG weekly report |
| **Scale** | FastAPI ×2 (50 endpoints) · **17,402** restaurants in SQLite · Next.js 16 PWA with 7 pages |
| **Infra** | Docker Compose 5-service (api·nlp·web·ollama·caddy) · Cloudflare Tunnel · runtime LLM toggle (Ollama ↔ Gemini) · automated demo deploy |
| **Tech** | FastAPI · Next.js 16 · KcELECTRA · ChromaDB · Ollama/Gemini · Docker · Caddy · TanStack Query |
| **Role** | Team |

📂 [Phase13&14 folder](./Phase13%2614)

---

### 2. OpenCV & ML Hybrid Defect Inspection System — *Phase 9* (Team Lead)

> **2-stage automatic inspection of 4 steel-surface defect types — with cross-domain validation proving "data > architecture"**

| | |
|------|------|
| **Problem** | Manufacturing quality-inspection automation — building a defect-classification pipeline at industrial scale (150K+ images) |
| **Data** | Kaggle Severstal 12,568 images → **150,816 patches** (256×256, stride=128, 50% overlap) |
| **Approach** | 2-stage (binary → 4-class) · OpenCV preprocessing · 7 ML models · DL (ResNet-18) · Autoencoder anomaly detection |
| **Results** | Stage 1 DL **90.87%** / Stage 2 DL **86.01%** / AE Recall **96.0%** · 8-tab Streamlit dashboard |
| **Key insight** | In Severstal→NEU cross-domain validation, ML **51.6%** > DL **14.4%** → demonstrated that *data matters more than architecture* for generalization |
| **Tech** | OpenCV · Scikit-learn · PyTorch · Autoencoder · Streamlit |
| **Role** | **Team Lead** (Vision-Q) |

📂 [Phase9 folder](./Phase9)

---

### 3. ML-Based Inventory Optimization WMS — *Phase 8* (Team Lead)

> **An inventory-optimization system spanning classification, regression, and unsupervised learning from a single dataset**

| | |
|------|------|
| **Problem** | Lack of WMS at SMB distributors (ERP adoption only 16.3%) → repeated overstock waste and stockouts |
| **Approach** | 4 sub-topics — stock-status classification · sales forecasting · expiry-risk prediction · ordering-strategy clustering + EOQ simulation |
| **Results** | LightGBM Acc **99%** · XGBoost **R²=0.948** · K-Means per-cluster ordering strategy · triple-cross-validated feature importance · SHAP interpretation |
| **Deliverable** | Streamlit WMS v3.5 — 7 pages, dual mode, 20+ ML models |
| **Tech** | Scikit-learn · XGBoost · LightGBM · K-Means · SHAP · Streamlit |
| **Role** | **Team Lead** (Good Fit) |

📂 [Phase8 folder](./Phase8)

---

### 4. Smoking & Stroke Association Analysis — *Phase 2*

> **Medical statistics leveraging my Statistics major — testing whether smoking is an independent risk factor even after controlling for confounders**

| | |
|------|------|
| **Research question** | After controlling for age, sex, BMI, alcohol, and physical activity, does smoking still raise stroke risk? |
| **Data** | CDC BRFSS 2020 — **319,795 individuals** × 18 variables (0% missing) |
| **Approach** | chi-square·Cramér's V → multivariate logistic regression (Crude → fully adjusted OR) → interaction/stratified analysis → VIF → ML/DL comparison |
| **Results** | Smoker incidence **5.17%** vs non-smoker 2.80% (1.85×) · still significant after full adjustment · XGBoost AUC **0.808** · PyTorch (Focal Loss) ensemble · SHAP interpretation |
| **Tech** | Pandas · statsmodels · Scikit-learn · XGBoost · PyTorch · SHAP |
| **Role** | Team |

📂 [Phase2 folder](./Phase2)

---

### 5. KBO Away-Game Companion — *Phase 12* 🌐

> **From data model to live service — a deployed full-stack web app with a Gemini Tool Calling chatbot**

| | |
|------|------|
| **Topic** | An all-in-one planner for KBO away-game fans across 10 clubs · 8 cities · 720 games/year (6 pages) |
| **Data → service** | scikit-learn win-probability model ported to TypeScript · 3-tier routing fallback (Kakao → OSRM → Haversine) |
| **AI integration** | Gemini 2.5 Flash Lite streaming chatbot + 6 Tool Calls + multi-agent |
| **Results** | **Live deployment** on Firebase App Hosting · mobile auto-tests **138/138 PASS** · 7 Secret Manager secrets · GitHub auto-rollout |
| **Tech** | Next.js 16 · React 19 · Gemini 2.5 · React-Leaflet · Cloud Firestore · Firebase App Hosting |
| **Role** | Team |

📂 [Phase12 folder](./Phase12) · 🌐 [Live Demo](https://my-web-app--mini12-310f5.asia-east1.hosted.app)

---

## 📚 All Projects (13)

| Phase | Project | Period | Field | Core Tech | Role |
|-------|---------|------|------|----------|------|
| **[1](./Phase1)** | Python Basics (Pygame FPS · mini-games · tkinter GUI) | 2025.12–2026.01 | Python | Pygame raycasting, tkinter, OOP | Solo |
| **[2](./Phase2)** ⭐ | Smoking & Stroke Association Analysis | 2026.01 | Medical Stats | Logistic regression, XGBoost (AUC 0.808), SHAP | Team |
| **[3](./Phase3)** | Esports Analysis (economy·equity·medical) | 2026.01–02 | Data Analysis | Pandas, statistics, visualization | Team |
| **[4](./Phase4)** | Climate Change Impact on Sauce Ingredients | 2026.02 | Data Collection | Crawling, time-series analysis | Team |
| **[5](./Phase5)** | Global Inland Hub Cities Comparison (Daegu) | 2026.02 | Data Viz | Matplotlib, Seaborn, Plotly | Team |
| **[6](./Phase6)** | Medical-AI Job-Trend Crawling & Analysis | 2026.02 | Web Crawling | Selenium, BeautifulSoup, morphological analysis | Team |
| **[7](./Phase7)** | Testing MBTI/Blood-Type Personality Theories | 2026.03 | Statistical Testing | NumPy, chi-square, ANOVA, t-test | Team |
| **[8](./Phase8)** ⭐ | ML Inventory Optimization WMS | 2026.03 | Machine Learning | LightGBM, XGBoost, K-Means, SHAP, Streamlit | **Lead** |
| **[9](./Phase9)** ⭐ | OpenCV & ML Defect Inspection | 2026.03 | Computer Vision | OpenCV, PyTorch, Autoencoder, Streamlit | **Lead** |
| **[10](./Phase10)** | AI Smart-Factory Quality Control | 2026.04 | Deep Learning | CNN, U-Net, YOLOv8, BERT | Team |
| **[11](./Phase11)** | HelchangGPT — NLP Fitness Coaching | 2026.04 | NLP | Ollama LLM, NER, sentiment analysis, React | Team |
| **[12](./Phase12)** ⭐ | Away-Game Companion (KBO) | 2026.04 | Full-stack/Cloud | Next.js 16, Firebase, Gemini Tool Calling | Team |
| **[13&14](./Phase13%2614)** ⭐ | Integrated Lunch-Recommendation AI Dashboard | 2026.04–05 | Full-stack AI | FastAPI×2, Next.js, RAG, KcELECTRA, Docker | Team |

> ⭐ = Featured (details under [Featured Projects](#-featured-projects) above)

---

## 🛠️ Skill-Growth Roadmap

```
Phase 1     Python basics        Pygame · tkinter · OOP
   │
Phase 2~3   Statistics·analysis  Logistic regression · XGBoost · multi-perspective analysis
   │
Phase 4~6   Collection·viz·crawl Selenium · BeautifulSoup · Plotly
   │
Phase 7     Statistical testing  NumPy · chi-square · ANOVA · t-test
   │
Phase 8     Machine learning     LightGBM · XGBoost · K-Means · SHAP
   │
Phase 9     Computer vision      OpenCV · ResNet-18 · Autoencoder
   │
Phase 10    Deep learning        CNN · U-Net · YOLOv8 · BERT
   │
Phase 11    NLP                  Ollama LLM · NER · sentiment analysis
   │
Phase 12    Full-stack/Cloud     Next.js 16 · Firebase · Gemini Tool Calling
   │
Phase 13&14 Integrated AI svc    FastAPI ×2 · RAG · KcELECTRA · Docker · Tunnel
```

---

## 📊 Project Scale

| Phase | Files | Key Deliverables |
|-------|---------|-----------|
| 1 | 73 | FPS game, 6 mini-games, medical-management GUI |
| 2 | 22 | Analysis report, visualization charts |
| 3 | 271 | 3-perspective analysis (economy/equity/medical) |
| 4 | 55 | Crawled data, analysis report |
| 5 | 163 | Interactive visualization, presentation materials |
| 6 | 370 | Crawling pipeline, NLP analysis |
| 7 | 153 | Statistical-testing report, visualization |
| 8 | 428 | Streamlit WMS v3.5, 4 sub-topic reports |
| 9 | 162 | 12 notebooks, 8-tab Streamlit, 5 reports |
| 10 | 150 | 4 sub-topic DL models, Streamlit dashboard |
| 11 | 149 | NLP pipeline, React frontend |
| 12 | 443 | Next.js 16 full-stack, live Firebase deployment |
| 13&14 | 457 | FastAPI ×2, Next.js PWA, RAG chatbot, 5-service Docker |
| **Total** | **~2,900** | **13 Phase projects completed** |

---

## 📫 Contact

| | |
|------|------|
| **GitHub** | [github.com/HorangEe02](https://github.com/HorangEe02) |
| **Email** | catlife9029@gmail.com |
| **Notion Portfolio** | [Open](https://www.notion.so/31879104c6f38039a53cfaa4b64ef712) |

---

*This repository collects the mini-projects completed during the Kyungpook National University K-Digital Training AI/Big Data Specialist Program (Cohort 12). Each Phase folder contains its own detailed README.*
