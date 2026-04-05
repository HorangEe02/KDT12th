import { useState } from "react";

const themes = [
  {
    id: "healthcare",
    icon: "🏥",
    title: "AI 기반 스마트 헬스케어 진단 보조 시스템",
    color: "#00d4aa",
    colorBg: "rgba(0,212,170,0.08)",
    colorBorder: "rgba(0,212,170,0.3)",
    narrative: "의료 현장에서 다양한 형태의 데이터(X-ray 이미지, MRI 영상, 진료 기록 텍스트, 약물 리뷰)를 딥러닝으로 분석하여 의사의 진단을 보조하는 통합 AI 시스템을 구축합니다.",
    why: "의료 분야는 CNN(이미지 분류), U-Net(세그먼테이션), BERT(텍스트 분류) 등 수업에서 배운 모든 기술을 자연스럽게 통합할 수 있는 최적의 도메인입니다. 데이터가 풍부하고, 사회적 임팩트가 높아 발표 시 주목도가 뛰어납니다.",
    recommended: true,
    subtopics: [
      {
        num: "A",
        label: "CNN 이미지 분류",
        title: "흉부 X-ray 폐렴 자동 진단",
        desc: "흉부 X-ray 이미지를 ResNet/DenseNet 전이학습으로 정상/폐렴을 분류합니다. Grad-CAM 히트맵으로 모델이 주목하는 폐 영역을 시각화하여 의료 AI의 설명 가능성(Explainability)을 시연합니다.",
        tech: ["ResNet / DenseNet", "전이학습", "이진 분류", "Grad-CAM"],
        datasets: [
          { name: "Chest X-Ray Images (Pneumonia)", detail: "5,863장 · 2클래스 · Train/Val/Test 분리 완료", url: "https://www.kaggle.com/datasets/paultimothymooney/chest-xray-pneumonia" },
          { name: "Chest X-ray (Covid-19 & Pneumonia)", detail: "6,432장 · 3클래스 (COVID/Pneumonia/Normal)", url: "https://www.kaggle.com/datasets/prashant268/chest-xray-covid19-pneumonia" }
        ]
      },
      {
        num: "B",
        label: "U-Net 세그먼테이션",
        title: "유방 초음파 병변 영역 분할",
        desc: "유방 초음파 이미지에서 U-Net을 사용하여 종양(양성/악성) 영역을 픽셀 단위로 세그먼테이션합니다. Dice Loss와 IoU 지표로 성능을 평가하고, Skip Connection의 효과를 실험합니다.",
        tech: ["U-Net", "Dice Loss / IoU", "세그먼테이션 마스크", "데이터 증강"],
        datasets: [
          { name: "Breast Ultrasound Images (BUSI)", detail: "780장 · 3클래스 + 세그먼테이션 마스크 포함", url: "https://www.kaggle.com/datasets/aryashah2k/breast-ultrasound-images-dataset" },
          { name: "2018 Data Science Bowl (Nuclei)", detail: "670장 · 세포핵 세그먼테이션 · U-Net 벤치마크", url: "https://www.kaggle.com/competitions/data-science-bowl-2018" }
        ]
      },
      {
        num: "C",
        label: "NLP 텍스트 분류",
        title: "의료 기록 텍스트 → 진료과 자동 분류",
        desc: "환자의 진료 기록(Medical Transcription) 텍스트를 BERT로 분석하여 해당 진료과(외과, 내과, 정형외과 등)를 자동 분류합니다. 수업에서 배운 BERT 파인튜닝과 토큰화를 직접 적용할 수 있습니다.",
        tech: ["BERT / KoBERT", "텍스트 분류", "토큰화 (WordPiece)", "파인튜닝"],
        datasets: [
          { name: "Medical Transcriptions (mtsamples)", detail: "4,998건 · 40개 진료과 · 진료 기록 텍스트", url: "https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions" },
          { name: "Medical Text (Cancer Doc Classification)", detail: "암 관련 의료 문서 텍스트 분류 데이터셋", url: "https://www.kaggle.com/datasets/falgunipatel19/biomedical-text-publication-classification" }
        ]
      },
      {
        num: "D",
        label: "NLP 감성 분석",
        title: "환자 약물 리뷰 감성 분석 및 만족도 예측",
        desc: "환자가 작성한 약물 복용 리뷰 텍스트를 Bi-LSTM 또는 BERT로 감성 분석(긍정/중립/부정)하고, 약물별 만족도를 예측합니다. 51,000건 이상의 풍부한 텍스트 데이터로 NLP 모델 성능 비교 실험이 가능합니다.",
        tech: ["BERT / Bi-LSTM", "감성 분석", "임베딩 (GloVe)", "3-클래스 분류"],
        datasets: [
          { name: "UCI ML Drug Review Dataset", detail: "51,408건 · 약물명/질환/리뷰/평점(1-10) 포함", url: "https://www.kaggle.com/datasets/jessicali9530/kuc-hackathon-winter-2018" },
          { name: "Drugs.com Reviews (Drugs Condition)", detail: "215,063건 · 약물별 리뷰 + 10점 만점 평점", url: "https://www.kaggle.com/datasets/rohanharode07/webmd-drug-reviews-dataset" }
        ]
      }
    ]
  },
  {
    id: "factory",
    icon: "🏭",
    title: "AI 기반 스마트 팩토리 품질관리 시스템",
    color: "#ff6b35",
    colorBg: "rgba(255,107,53,0.08)",
    colorBorder: "rgba(255,107,53,0.3)",
    narrative: "제조 공정에서 발생하는 다양한 데이터(제품 이미지, 표면 결함, PCB 기판, 설비 로그)를 딥러닝으로 분석하여 품질 검사와 설비 유지보수를 자동화하는 통합 AI 시스템을 구축합니다.",
    why: "제조업은 객체 탐지(YOLO)와 세그먼테이션(U-Net)의 대표적 응용 분야이며, 설비 로그 분석에 NLP를 자연스럽게 접목할 수 있습니다. 실제 산업 현장에서의 수요가 매우 높은 주제입니다.",
    recommended: false,
    subtopics: [
      {
        num: "A",
        label: "CNN 이미지 분류",
        title: "주조 제품 불량/정상 자동 분류",
        desc: "주조 공정에서 생산된 제품 상단 이미지를 CNN(ResNet/VGG)으로 분류하여 불량 여부를 판별합니다. 전이학습과 Grad-CAM으로 결함 영역을 시각화합니다.",
        tech: ["ResNet / VGG", "전이학습", "이진 분류", "Grad-CAM"],
        datasets: [
          { name: "Casting Product Image Data", detail: "7,348장 · 2클래스 (defective/ok) · 300×300", url: "https://www.kaggle.com/datasets/ravirajsinh45/real-life-industrial-dataset-of-casting-product" },
          { name: "MVTec Anomaly Detection Dataset", detail: "5,000+ 이미지 · 15개 카테고리 · 산업 검사 벤치마크", url: "https://www.mvtec.com/company/research/datasets/mvtec-ad" }
        ]
      },
      {
        num: "B",
        label: "U-Net 세그먼테이션",
        title: "철강 표면 결함 영역 세그먼테이션",
        desc: "철강 표면 이미지에서 4가지 유형의 결함 영역을 U-Net으로 픽셀 단위 세그먼테이션합니다. Kaggle 대회 데이터를 활용하여 실제 산업 품질 검사를 시뮬레이션합니다.",
        tech: ["U-Net / DeepLabV3", "RLE 마스크", "Dice Loss", "다중 클래스 세그먼테이션"],
        datasets: [
          { name: "Severstal: Steel Defect Detection", detail: "12,568장 · 4가지 결함 유형 · Kaggle 공식 대회", url: "https://www.kaggle.com/c/severstal-steel-defect-detection" },
          { name: "NEU Surface Defect Database", detail: "1,800장 · 6가지 결함 유형", url: "http://faculty.neu.edu.cn/yunhyan/NEU_surface_defect_database.html" }
        ]
      },
      {
        num: "C",
        label: "YOLO 객체탐지",
        title: "PCB 기판 결함 자동 탐지",
        desc: "인쇄회로기판(PCB) 이미지에서 YOLOv8로 누락, 단락, 스퍼 등 6종 결함을 실시간 탐지합니다. 수업의 YOLO 워크플로우를 그대로 적용할 수 있습니다.",
        tech: ["YOLOv8", "바운딩 박스", "mAP 평가", "NMS"],
        datasets: [
          { name: "PCB Defects Dataset", detail: "693장 · 6가지 결함 · XML 어노테이션", url: "https://www.kaggle.com/datasets/akhatova/pcb-defects" },
          { name: "DeepPCB (GitHub)", detail: "1,500 이미지 쌍 · 결함 탐지 벤치마크", url: "https://github.com/tangsanli5201/DeepPCB" }
        ]
      },
      {
        num: "D",
        label: "NLP 텍스트 분류",
        title: "설비 고장 유형 예측 (유지보수 로그 분석)",
        desc: "제조 설비의 센서 데이터와 유지보수 로그를 분석하여 고장 유형(열 방출, 전력 이상, 마모 등)을 분류·예측합니다. 텍스트+수치 데이터를 결합한 멀티모달 접근이 가능합니다.",
        tech: ["LSTM / BERT", "텍스트 분류", "시계열 분석", "멀티모달"],
        datasets: [
          { name: "Machine Predictive Maintenance", detail: "10,000건 · 설비 고장 유형 5종 분류", url: "https://www.kaggle.com/datasets/shivamb/machine-predictive-maintenance-classification" },
          { name: "AI4I 2020 Predictive Maintenance", detail: "10,000건 · 센서 데이터 + 고장 레이블", url: "https://www.kaggle.com/datasets/stephanmatzka/predictive-maintenance-dataset-ai4i-2020" }
        ]
      }
    ]
  },
  {
    id: "driving",
    icon: "🚗",
    title: "AI 기반 자율주행 통합 인식 시스템",
    color: "#5b8def",
    colorBg: "rgba(91,141,239,0.08)",
    colorBorder: "rgba(91,141,239,0.3)",
    narrative: "자율주행 차량이 도로 위 객체를 탐지하고, 주행 가능 영역을 인식하며, 교통 표지판을 분류하고, 교통 사고 보고서를 자동 분석하는 통합 비전+NLP 시스템을 구축합니다.",
    why: "자율주행은 YOLO(객체탐지)의 가장 대표적인 응용이며, U-Net(도로 세그먼테이션), CNN(표지판 분류)을 포괄합니다. 교통 사고 데이터의 텍스트 분석으로 NLP를 접목할 수 있습니다.",
    recommended: false,
    subtopics: [
      {
        num: "A",
        label: "YOLO 객체탐지",
        title: "주행 영상 차량·보행자·신호등 실시간 탐지",
        desc: "전방 카메라 영상에서 YOLOv8로 차량, 보행자, 트럭, 신호등 등을 실시간 탐지합니다. YOLO의 전체 파이프라인(데이터→학습→평가→추론)을 경험합니다.",
        tech: ["YOLOv8", "전이학습", "mAP@0.5", "실시간 추론"],
        datasets: [
          { name: "Self-Driving Cars (Kaggle)", detail: "전방 카메라 이미지 · 다중 클래스 바운딩 박스", url: "https://www.kaggle.com/datasets/alincijov/self-driving-cars" },
          { name: "Udacity Self-Driving Car (Roboflow)", detail: "15,000+ 이미지 · 512×512 · YOLO 호환", url: "https://public.roboflow.com/object-detection/self-driving-car" }
        ]
      },
      {
        num: "B",
        label: "U-Net 세그먼테이션",
        title: "주행 가능 영역 및 차선 세그먼테이션",
        desc: "도로 이미지에서 U-Net으로 '주행 가능 영역'과 '차선'을 픽셀 단위로 분할합니다. 자율주행의 경로 계획에 필수적인 핵심 비전 모듈입니다.",
        tech: ["U-Net", "시맨틱 세그먼테이션", "IoU / mIoU", "차선 인식"],
        datasets: [
          { name: "BDD100K (Drivable Area)", detail: "100K 프레임 · 주행 영역 + 차선 마스크", url: "https://bdd-data.berkeley.edu/" },
          { name: "Cityscapes Dataset", detail: "5,000장 · 30개 클래스 · 도시 세그먼테이션", url: "https://www.cityscapes-dataset.com/" }
        ]
      },
      {
        num: "C",
        label: "CNN 이미지 분류",
        title: "교통 표지판 자동 인식 (43개 클래스)",
        desc: "다양한 조건(밝기, 회전, 흐림)의 교통 표지판 이미지를 CNN으로 43개 클래스로 분류합니다. 데이터 증강의 효과를 실험하기 좋은 주제입니다.",
        tech: ["CNN (EfficientNet)", "다중 분류", "데이터 증강", "강건성 평가"],
        datasets: [
          { name: "GTSRB (German Traffic Sign)", detail: "50,000+ 이미지 · 43클래스 · 표지판 인식 표준", url: "https://www.kaggle.com/datasets/meowmeowmeowmeowmeow/gtsrb-german-traffic-sign" },
          { name: "KITTI Vision Benchmark", detail: "2D/3D 탐지 · 종합 자율주행 벤치마크", url: "https://www.cvlibs.net/datasets/kitti/" }
        ]
      },
      {
        num: "D",
        label: "NLP 텍스트 분류",
        title: "교통 사고 보고서 텍스트 분석 및 심각도 분류",
        desc: "교통 사고 보고서/뉴스 텍스트를 BERT/LSTM으로 분석하여 사고 유형 또는 심각도를 자동 분류합니다. 자율주행 안전 시스템의 데이터 기반 의사결정을 보조합니다.",
        tech: ["BERT / LSTM", "텍스트 분류", "감성/심각도 분석", "TF-IDF"],
        datasets: [
          { name: "US Accidents Dataset", detail: "7.7M건 · 사고 심각도/위치/날씨/설명 텍스트", url: "https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents" },
          { name: "UK Road Safety: Traffic Accidents", detail: "영국 교통 사고 데이터 · 사고 유형/심각도", url: "https://www.kaggle.com/datasets/tsiaras/uk-road-safety-accidents-and-vehicles" }
        ]
      }
    ]
  }
];

const techColors = {
  "ResNet / DenseNet": "#ef4444", "ResNet / VGG": "#ef4444",
  "전이학습": "#f97316", "이진 분류": "#eab308",
  "Grad-CAM": "#84cc16", "U-Net": "#22c55e",
  "Dice Loss / IoU": "#14b8a6", "세그먼테이션 마스크": "#06b6d4",
  "데이터 증강": "#0ea5e9", "BERT / KoBERT": "#6366f1",
  "텍스트 분류": "#8b5cf6", "토큰화 (WordPiece)": "#a855f7",
  "파인튜닝": "#d946ef", "BERT / Bi-LSTM": "#ec4899",
  "감성 분석": "#f43f5e", "임베딩 (GloVe)": "#fb7185",
  "3-클래스 분류": "#fbbf24", "YOLOv8": "#ff6b35",
  "바운딩 박스": "#fb923c", "mAP 평가": "#fdba74",
  "NMS": "#fed7aa", "LSTM / BERT": "#818cf8",
  "시계열 분석": "#67e8f9", "멀티모달": "#c084fc",
  "U-Net / DeepLabV3": "#22c55e", "RLE 마스크": "#86efac",
  "Dice Loss": "#4ade80", "다중 클래스 세그먼테이션": "#a3e635",
  "mAP@0.5": "#fde047", "실시간 추론": "#fcd34d",
  "시맨틱 세그먼테이션": "#2dd4bf", "IoU / mIoU": "#5eead4",
  "차선 인식": "#99f6e4", "CNN (EfficientNet)": "#f87171",
  "다중 분류": "#fca5a5", "강건성 평가": "#fecaca",
  "BERT / LSTM": "#a78bfa", "감성/심각도 분석": "#c4b5fd",
  "TF-IDF": "#ddd6fe",
};

const labelStyles = {
  "CNN 이미지 분류": { bg: "#1e293b", border: "#ef4444", text: "#fca5a5" },
  "U-Net 세그먼테이션": { bg: "#1e293b", border: "#22c55e", text: "#86efac" },
  "YOLO 객체탐지": { bg: "#1e293b", border: "#f97316", text: "#fdba74" },
  "NLP 텍스트 분류": { bg: "#1e293b", border: "#8b5cf6", text: "#c4b5fd" },
  "NLP 감성 분석": { bg: "#1e293b", border: "#ec4899", text: "#f9a8d4" },
};

export default function App() {
  const [selected, setSelected] = useState("healthcare");
  const theme = themes.find(t => t.id === selected);

  return (
    <div style={{ background: "#0a0a0f", minHeight: "100vh", color: "#e8e8f0", fontFamily: "'Noto Sans KR', system-ui, sans-serif", padding: "24px 16px" }}>
      <div style={{ maxWidth: 960, margin: "0 auto" }}>

        {/* Header */}
        <div style={{ textAlign: "center", padding: "40px 0 24px" }}>
          <h1 style={{ fontSize: "1.8em", fontWeight: 900, letterSpacing: "-0.5px", background: "linear-gradient(135deg, #ff6b35, #00d4aa, #5b8def)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", marginBottom: 8 }}>
            통합 대주제 → 4개 소주제 브레인스토밍
          </h1>
          <p style={{ color: "#8888a0", fontSize: "0.9em", maxWidth: 520, margin: "0 auto" }}>
            하나의 대주제 아래 CNN · U-Net · YOLO · NLP를 모두 포괄하는 미니프로젝트 설계
          </p>
        </div>

        {/* Theme Tabs */}
        <div style={{ display: "flex", gap: 8, marginBottom: 32, flexWrap: "wrap", justifyContent: "center" }}>
          {themes.map(t => (
            <button key={t.id} onClick={() => setSelected(t.id)} style={{
              padding: "10px 20px", borderRadius: 12, border: `1.5px solid ${selected === t.id ? t.color : "#2a2a3a"}`,
              background: selected === t.id ? t.colorBg : "#12121a", color: selected === t.id ? t.color : "#8888a0",
              cursor: "pointer", fontSize: "0.88em", fontWeight: 600, transition: "all 0.2s", fontFamily: "inherit",
              position: "relative"
            }}>
              {t.icon} {t.title.split(" ").slice(0, 3).join(" ")}
              {t.recommended && <span style={{ position: "absolute", top: -8, right: -8, background: "#ffd700", color: "#000", fontSize: "0.65em", padding: "2px 6px", borderRadius: 6, fontWeight: 700 }}>추천</span>}
            </button>
          ))}
        </div>

        {/* Theme Detail */}
        {theme && (
          <div>
            {/* Theme Header Card */}
            <div style={{ background: "#12121a", border: `1.5px solid ${theme.colorBorder}`, borderRadius: 16, padding: 28, marginBottom: 28 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 14 }}>
                <span style={{ fontSize: "2em" }}>{theme.icon}</span>
                <div>
                  <h2 style={{ fontSize: "1.35em", fontWeight: 800, color: theme.color, margin: 0 }}>{theme.title}</h2>
                  {theme.recommended && <span style={{ fontSize: "0.72em", background: "rgba(255,215,0,0.15)", color: "#ffd700", padding: "3px 8px", borderRadius: 6, fontWeight: 600, marginTop: 4, display: "inline-block" }}>🏆 1순위 추천 — 데이터 풍부 · NLP 자연스러운 연결 · 발표 임팩트 최고</span>}
                </div>
              </div>
              <p style={{ color: "#c0c0d0", fontSize: "0.92em", lineHeight: 1.8, marginBottom: 14 }}>{theme.narrative}</p>
              <p style={{ color: "#8888a0", fontSize: "0.85em", lineHeight: 1.7, padding: "12px 16px", background: "rgba(255,255,255,0.03)", borderRadius: 10, borderLeft: `3px solid ${theme.color}` }}>
                💡 <strong style={{ color: "#c0c0d0" }}>왜 이 주제인가?</strong> {theme.why}
              </p>
            </div>

            {/* Structure Overview */}
            <div style={{ background: "#12121a", border: "1px solid #2a2a3a", borderRadius: 16, padding: 24, marginBottom: 28 }}>
              <h3 style={{ fontSize: "0.95em", fontWeight: 700, marginBottom: 16, color: "#c0c0d0" }}>📐 프로젝트 구조 (팀원 4명 기준)</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: 10 }}>
                {theme.subtopics.map((s, i) => {
                  const ls = labelStyles[s.label] || { bg: "#1e293b", border: "#666", text: "#ccc" };
                  return (
                    <div key={i} style={{ background: ls.bg, border: `1px solid ${ls.border}40`, borderRadius: 10, padding: "12px 14px", textAlign: "center" }}>
                      <div style={{ fontSize: "0.7em", color: ls.text, fontWeight: 600, marginBottom: 4, fontFamily: "'JetBrains Mono', monospace" }}>팀원 {s.num} — {s.label}</div>
                      <div style={{ fontSize: "0.82em", fontWeight: 600, color: "#e0e0e8" }}>{s.title.length > 18 ? s.title.slice(0, 18) + "…" : s.title}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Subtopic Cards */}
            {theme.subtopics.map((s, idx) => {
              const ls = labelStyles[s.label] || { bg: "#1e293b", border: "#666", text: "#ccc" };
              return (
                <div key={idx} style={{ background: "#12121a", border: "1px solid #2a2a3a", borderRadius: 16, padding: 24, marginBottom: 16 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8, marginBottom: 14 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.75em", fontWeight: 700, padding: "4px 10px", borderRadius: 6, background: theme.colorBg, color: theme.color }}>{s.num}</span>
                      <span style={{ fontSize: "0.78em", fontWeight: 600, padding: "4px 10px", borderRadius: 6, background: `${ls.border}18`, color: ls.text, border: `1px solid ${ls.border}40` }}>{s.label}</span>
                    </div>
                  </div>

                  <h3 style={{ fontSize: "1.1em", fontWeight: 700, marginBottom: 10 }}>{s.title}</h3>
                  <p style={{ color: "#9999b0", fontSize: "0.88em", lineHeight: 1.8, marginBottom: 16 }}>{s.desc}</p>

                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 18 }}>
                    {s.tech.map((t, ti) => (
                      <span key={ti} style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.72em", padding: "3px 8px", borderRadius: 5, background: "rgba(255,255,255,0.05)", color: techColors[t] || "#999", border: "1px solid rgba(255,255,255,0.08)" }}>{t}</span>
                    ))}
                  </div>

                  <div style={{ background: "#0f0f18", borderRadius: 12, padding: 16, border: "1px solid #1e1e2e" }}>
                    <div style={{ fontSize: "0.72em", fontWeight: 600, color: "#8888a0", textTransform: "uppercase", letterSpacing: 1, marginBottom: 12 }}>📂 활용 가능 데이터셋</div>
                    {s.datasets.map((d, di) => (
                      <div key={di} style={{ display: "flex", gap: 10, padding: "8px 0", borderBottom: di < s.datasets.length - 1 ? "1px solid rgba(255,255,255,0.04)" : "none" }}>
                        <div style={{ width: 6, height: 6, borderRadius: "50%", background: theme.color, marginTop: 8, flexShrink: 0 }} />
                        <div>
                          <div style={{ fontWeight: 600, fontSize: "0.88em", marginBottom: 3 }}>{d.name}</div>
                          <div style={{ fontSize: "0.78em", color: "#8888a0", marginBottom: 4 }}>{d.detail}</div>
                          <a href={d.url} target="_blank" rel="noreferrer" style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "0.72em", color: "#6b9fff", textDecoration: "none", wordBreak: "break-all" }}>{d.url}</a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}

            {/* Comparison Table */}
            <div style={{ background: "#12121a", border: "1px solid #2a2a3a", borderRadius: 16, padding: 24, marginTop: 28 }}>
              <h3 style={{ fontSize: "1em", fontWeight: 700, marginBottom: 16 }}>📊 3개 대주제 비교 요약</h3>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.82em" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid #2a2a3a" }}>
                      {["평가 항목", "🏥 헬스케어", "🏭 스마트 팩토리", "🚗 자율주행"].map((h, i) => (
                        <th key={i} style={{ padding: "10px 12px", textAlign: "left", color: "#8888a0", fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ["데이터 접근성", "⭐⭐⭐ 매우 풍부", "⭐⭐⭐ 풍부", "⭐⭐ 보통"],
                      ["NLP 자연스러움", "⭐⭐⭐ 최고", "⭐⭐ 양호", "⭐⭐ 양호"],
                      ["2일 완성 가능성", "⭐⭐⭐ 높음", "⭐⭐⭐ 높음", "⭐⭐ 보통"],
                      ["발표 임팩트", "⭐⭐⭐ 최고", "⭐⭐⭐ 높음", "⭐⭐⭐ 높음"],
                      ["수업 연관성", "⭐⭐⭐ CNN+U-Net+NLP", "⭐⭐⭐ CNN+YOLO+U-Net", "⭐⭐⭐ YOLO+U-Net+CNN"],
                      ["종합 추천", "🥇 1순위", "🥈 2순위", "🥉 3순위"],
                    ].map((row, ri) => (
                      <tr key={ri} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                        {row.map((cell, ci) => (
                          <td key={ci} style={{ padding: "10px 12px", color: ci === 0 ? "#c0c0d0" : "#9999b0", fontWeight: ci === 0 ? 600 : 400 }}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}

        <div style={{ textAlign: "center", marginTop: 40, padding: 16, color: "#666", fontSize: "0.78em", borderTop: "1px solid #1e1e2e" }}>
          K-Digital Training 딥러닝 12기 · 통합 대주제 브레인스토밍 · 2026.03.31
        </div>
      </div>
    </div>
  );
}
