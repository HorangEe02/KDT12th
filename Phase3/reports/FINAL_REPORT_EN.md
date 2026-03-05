# Final Report: Can Esports Be Recognized as a Sport?

> **KDT 12th Mini Project - Phase 3 | Team 1**
> **Analysis Period**: January 2025
> **Total Data Analyzed**: 470,000+ records across 12+ major datasets

---

## 1. Introduction

### 1.1 Background

The global esports market has grown explosively, reaching $18-20 billion by 2024. Despite this rapid expansion, the question of whether esports qualifies as a legitimate "sport" remains actively debated in policy, media, and academic circles. This debate carries tangible consequences, including eligibility for government support, military service exemptions, athlete honors, and institutional investment.

### 1.2 Research Objective

This project investigates whether **esports can be recognized as a sport based on data-driven evidence**, analyzing the question from three complementary perspectives:

| Module | Perspective | Core Question |
|--------|-------------|---------------|
| **01_economic** | Economic | Does esports share the same economic structure as traditional sports? |
| **02_equality** | Structural Equality | Is esports equivalent to traditional sports in complexity and growth? |
| **03_medical** | Physical / Medical | Do esports players demonstrate sport-level physical and cognitive demands? |

### 1.3 Methodology

- **Datasets**: 24 Kaggle datasets, web-crawled data (Twitch, Google Trends), government surveys
- **Analysis Tools**: Python (pandas, matplotlib, seaborn, scipy, plotly), Jupyter Notebooks
- **Statistical Methods**: Gini coefficient, Lorenz curves, Welch's t-test, Cohen's d effect size, cosine similarity, regression analysis, ANOVA, K-means clustering

---

## 2. Part A: Economic Analysis

### 2.1 Market Size Comparison

| Category | Market Size (2024) |
|----------|-------------------|
| Soccer | $280B |
| NFL | $180B |
| **Esports** | **$18-20B** |
| Archery | $2B |
| Fencing | $1.5B |
| Shooting | $3B |

Esports already exceeds the market size of several Olympic-recognized sports (archery, fencing, shooting), demonstrating economic viability comparable to established sport categories.

### 2.2 Prize Pool Growth

| Year | Total Prize Pool | Multiplier |
|------|-----------------|------------|
| 2010 | $5M | 1x |
| 2015 | $61M | 12x |
| 2020 | $173M | 35x |
| 2023 | $270M | **54x** |

- **CAGR**: 25% (versus 3-5% for traditional sports)
- Top games by cumulative prizes: Dota 2 ($360M), Fortnite ($191M), CS:GO ($162M)

### 2.3 Income Distribution (Gini Coefficient)

| Sport | Gini Coefficient |
|-------|-----------------|
| NFL | 0.607 |
| **Esports** | **0.616 - 0.937** |
| Soccer | 0.715 |

Esports exhibits the same "winner-takes-all" income distribution as traditional sports, confirming structural economic homogeneity.

### 2.4 Revenue Structure

| Revenue Source | Esports | Traditional Sports |
|---------------|---------|-------------------|
| Media Rights | 25% | 30-40% |
| Sponsorship | 40% | 25-35% |
| Tickets & Events | 10% | 15-20% |
| Merchandise | 15% | 10-15% |
| **Media + Sponsorship** | **65%** | **60-75%** |

Both sectors derive the majority of revenue from media rights and sponsorship, confirming identical business model patterns.

### 2.5 ARPU (Average Revenue Per User)

| Sport | ARPU | Growth Rate |
|-------|------|-------------|
| NFL | $105.88 | 5.2% |
| Soccer | $45.67 | 8.1% |
| **Esports** | **$2.34** | **37.3%** |

Despite a lower absolute ARPU (reflecting market maturity), esports demonstrates the highest growth rate, indicating significant future monetization potential.

### 2.6 Part A Conclusion

Esports shares the same economic DNA as traditional sports: identical income distribution curves, parallel revenue structures, and a growth trajectory that compresses 50 years of traditional sports development into 15 years.

---

## 3. Part B: Structural Equality Analysis

### 3.1 Strategy 1 - Economic Structure Homogeneity

Lorenz curve analysis confirms that esports follows the same wealth concentration pattern as traditional sports. The Gini coefficient of 0.616 places esports between the NFL (0.607) and soccer (0.715), well within the established range of professional sports.

### 3.2 Strategy 2 - Cognitive Load as Physical Activity

#### Actions Per Minute (APM)

| Game | Pro Player | Amateur | Ratio |
|------|-----------|---------|-------|
| StarCraft II | 350 APM | 80 APM | 4.4x |
| League of Legends | 250 APM | 50 APM | 5.0x |
| Dota 2 | 200 APM | 60 APM | 3.3x |

#### Cognitive Performance Metrics

| Metric | Pro Esports | General Population | Advantage |
|--------|------------|-------------------|-----------|
| Reaction Time | 150ms | 250ms | 1.7x faster |
| Precision Rate | 98% | 85% | +13%p |
| Simultaneous Objects | 12 | 7 | 1.7x more |

These cognitive-motor demands are equivalent to those observed in gymnastics and competitive shooting, supporting the argument that esports involves sport-level physical-cognitive engagement.

### 3.3 Strategy 3 - Growth Trajectory Equivalence

| Period | Esports | Traditional Sports |
|--------|---------|-------------------|
| Starting Point | $130M (2010) | Varied |
| Current | $1.87B (2023) | $180-280B |
| Growth Factor | 14x in 14 years | 8-15x in 50 years |
| CAGR | 25% | 3-10% |

Esports has compressed 50 years of traditional sports market development into approximately 15 years, following the same S-curve growth pattern at an accelerated rate.

### 3.4 Strategy 4 - Role Specialization

Cosine similarity analysis between soccer and esports positions reveals **98.8% structural overlap**:

| Soccer Position | Esports Equivalent | Function |
|----------------|-------------------|----------|
| Midfielder | Jungler | Game orchestration |
| Striker | ADC (Carry) | Primary damage output |
| Defender | Top Laner | Line/zone maintenance |
| Goalkeeper | Support | Team protection |

This demonstrates identical levels of tactical complexity and professional role differentiation.

### 3.5 Comprehensive Scoring

| Dimension | Score |
|-----------|-------|
| Economic Structure | 75 / 100 |
| Cognitive Load | 85 / 100 |
| Growth Trajectory | 90 / 100 |
| Role Specialization | 82 / 100 |
| **Overall** | **83 / 100** |

---

## 4. Part C: Medical and Physiological Analysis

### 4.1 Peak Age Distribution

| Sport Category | Average Peak Age |
|---------------|-----------------|
| Gymnastics | 21.5 years |
| **Esports** | **22.1 years** |
| Swimming | 22.2 years |
| Soccer | 25.0 years |
| Golf | 29.5 years |
| Shooting | 31.2 years |

Esports players peak at ages consistent with "precision/explosive movement" sports (gymnastics, swimming), not endurance sports. This suggests that esports performance depends on reaction speed and neural processing speed, which decline with age similarly to physical precision sports.

### 4.2 Heart Rate Analysis

| Context | Heart Rate (BPM) |
|---------|-----------------|
| General Population (rest) | 72 |
| Chess (competition) | 120 |
| Shooting (competition) | 140 |
| **Esports (competition)** | **82.5 (avg), 163 (max)** |

- Average increase during play: **+14.6%** above resting rate
- Maximum observed: **163 BPM** (moderate-to-high intensity)
- Mental stress translates to measurable cardiovascular responses, comparable to recognized mind-sports and precision sports

### 4.3 Career-Performance Relationship

| Sport | R² Value | Interpretation |
|-------|----------|---------------|
| **Esports** | **0.851** | Strong skill-based progression |
| Soccer | 0.001 | Weak relationship |

The high R² value in esports indicates that accumulated practice hours strongly predict performance outcomes, confirming a skill-based competitive structure identical to traditional sports.

### 4.4 Statistical Testing

| Test | Statistic | p-value | Interpretation |
|------|-----------|---------|---------------|
| Welch's t-test (age) | t = -24.76 | p < 0.001 | Highly significant |
| Cohen's d | -1.448 | - | Large effect size |

The peak age of esports players is statistically distinct from traditional sports overall, but clusters with precision-based sports when analyzed by subcategory.

### 4.5 Position Competency Comparison

Radar chart analysis across 6 dimensions shows **99%+ similarity** between esports and soccer positions:

1. Reaction Speed
2. Field/Map Vision
3. Teamwork & Communication
4. Tactical Understanding
5. Individual Mechanics
6. Leadership & Shot-calling

### 4.6 Physiological Scoring

| Assessment Area | Initial Score | Revised Score |
|----------------|--------------|---------------|
| Physical/Cognitive Demand | 40 / 100 | **70 / 100** |
| Overall Sport Recognition | 74.75 / 100 | **76.25 / 100** |

After supplementary sensor data analysis (IMU, EMG, GSR, EEG), the physical/cognitive demand score was revised upward, reflecting measurable physiological stress during competition.

---

## 5. Key Findings Summary

| # | Finding | Evidence |
|---|---------|----------|
| 1 | **Economic Structure Match** | Gini coefficient 0.616 (between NFL 0.607 and Soccer 0.715) |
| 2 | **Accelerated Growth** | 25% CAGR vs 3-5% for traditional sports |
| 3 | **Cognitive-Motor Demands** | Pro APM 200-350 (4-5x amateur), 150ms reaction time |
| 4 | **Role Specialization** | 98.8% cosine similarity with soccer positions |
| 5 | **Peak Age Alignment** | 22.1 years (matches gymnastics 21.5, swimming 22.2) |
| 6 | **Cardiovascular Response** | 14.6% heart rate increase, max 163 BPM during play |
| 7 | **Skill-Based Progression** | R² = 0.851 (career hours predict performance) |
| 8 | **Revenue Model Parity** | 65% from media + sponsorship (same as traditional sports) |

---

## 6. Conclusion

### 6.1 Overall Assessment

This analysis provides **multiple independent lines of evidence** supporting the recognition of esports as a sport:

- **Economically**: Esports operates under the same business model, income distribution, and market dynamics as traditional sports.
- **Structurally**: Professional role specialization, growth trajectory, and competitive complexity match established sports.
- **Physiologically**: Measurable cognitive-motor demands, cardiovascular stress, and age-dependent performance decline parallel precision-based athletic disciplines.

### 6.2 Composite Score

| Module | Dimension | Score |
|--------|-----------|-------|
| Part A | Economic | 75 / 100 |
| Part B | Structural | 83 / 100 |
| Part C | Medical | 76.25 / 100 |
| **Overall** | **Composite** | **~78 / 100** |

### 6.3 Policy Implications

Based on the data-driven evidence presented:

1. **Athlete Recognition**: Esports players demonstrate sport-level skill progression, physical stress, and competitive structure
2. **Institutional Support**: Market economics justify government and institutional investment
3. **Educational Integration**: Cognitive benefits and structured competition support educational applications
4. **International Recognition**: Data supports continued integration into multi-sport events (Asian Games, potential Olympic inclusion)

### 6.4 Final Statement

> **"Esports can be recognized as a sport on data-backed grounds."**
> Multiple independent analyses across economic, structural, and medical dimensions converge on the same conclusion: esports meets the empirical criteria for sport classification.

---

## 7. Data Sources

### Kaggle Datasets
- Esports Earnings 1998-2023
- Esports Performance Rankings and Results
- League of Legends (multiple datasets)
- Top Games on Twitch 2016-2023
- Athlete Physiological Dataset
- Esports Sensors Dataset (IMU, EMG, GSR, EEG)
- FIFA EDA Stats
- NFL Contract and Draft Data
- Football Player Salaries
- And 15+ additional datasets

### External Sources
- Twitch API Data
- Google Trends
- 2025 Esports Industry Survey (Government)
- Newzoo Esports Market Reports

### Total Records Analyzed
- **470,000+** data points across all modules

---

## 8. Project Structure

```
phase3/
├── 01_economic/       Economic analysis (initial → enhanced → final)
├── 02_equality/       Structural equality analysis (initial → enhanced_v1/v2 → final)
├── 03_medical/        Medical/physiological analysis (initial → enhanced_v1/v2 → final)
├── data/              All datasets (raw CSV + ZIP archives)
├── presentation/      Final deliverables (PPTX, PDF, per-module reports)
├── reference/         Reference materials and supplementary analyses
└── archive/           Original backup files
```

---

*This report was compiled from the comprehensive data analysis conducted during KDT 12th Mini Project Phase 3.*
