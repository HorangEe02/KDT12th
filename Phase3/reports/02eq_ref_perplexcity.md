e스포츠와 전통 스포츠의 “대중적 인기(시청 수요, 팬 규모, 산업 규모 등)”를 비교 분석하려면, 단일 지표보다 여러 데이터셋을 조합해서 보는 방식이 적합합니다.[1][2][3]

## 분석에 쓸 수 있는 Kaggle 데이터셋

아래는 e스포츠·게임/전통 스포츠 관련 지표를 뽑아볼 수 있는 Kaggle 데이터셋들입니다.[4][5][6][7]

| 목적             | 데이터셋                                                                    | 주요 필드(예시)                        | 활용 아이디어                                                            |
| -------------- | ----------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------ |
| e스포츠·게임 시청/트렌드 | Video Game Trends Analysis with Streaming Data (Kaggle Notebook 예시) [4] | 스트리밍 플랫폼별 시청 시간, 평균 동시 시청자, 연도/월 | 연도별 e스포츠 관련 게임(LoL, Dota2, Valorant 등) 시청 시간 추이 vs 스포츠 게임 카테고리 비교. |
| 게임 산업 트렌드      | Gaming Industry Trends (1000 Rows) [6]                                  | 장르, 플랫폼, 매출, 플레이어 행동             | “e스포츠 종목에 해당하는 게임(예: MOBA, FPS)” 매출·플레이어 수 vs 비 e스포츠 장르 비교.        |
| 인기 게임 메타       | Top Games Dataset 🎮📊 [7]                                              | 게임명, 장르, 인기 지표(다운로드/평점 등)        | 상위 인기 게임 중 e스포츠 타이틀 비중, 장르별 인기 구조 분석.                              |
| 장기 게임 로그(스팀)   | game dataset (steam_uncleaned.csv 등) [5]                                | 날짜, 조회수/플레이 수 등                  | 2010년 이후 게임 관심도의 장기 추세, e스포츠 타이틀 vs 기타 장르 관심 비교.                   |

이 데이터들만으로 “전통 스포츠 vs e스포츠”를 직접 1:1 비교하기는 어렵지만,  
e스포츠 측 “대중성(시청·참여·매출)”을 수량화할 수 있고, 아래의 공공/연구 데이터와 조합하면 비교 구조를 만들 수 있습니다.[2][3][1]

## 전통 스포츠·e스포츠 비교에 쓸 공공/연구 데이터

직접 Kaggle에 “sports vs esports”가 같이 정리된 데이터는 드물기 때문에, 보통은 다음과 같이 **연구용/공공 통계를 따로 가져와 매칭**합니다.[3][1][2]

- WPI “Sports vs Esports” 연구 데이터  
  - 논문/보고서에서 FIFA 월드컵, NFL 슈퍼볼, MLB, NBA 등과 LoL Worlds, Dota2 International 등 e스포츠 결승의 **평균 동시 시청자(Concurrent Viewers)**, 총 시청자 수 등을 수집해 비교합니다.[1][3]
  - 이 자료에 따르면 월드컵·슈퍼볼에 비하면 여전히 전통 스포츠가 압도적이지만, LoL Worlds, Dota2 International 등 e스포츠 결승은 다른 많은 프로 스포츠 리그 결승과 비슷하거나 더 높은 시청자를 기록한 사례가 있습니다.[3][1]
  - 방법: 보고서에 수록된 표/그래프의 수치를 직접 추출하여 CSV로 재구성한 뒤, Kaggle에서 가져온 e스포츠 관련 스트리밍 지표와 함께 분석 테이블을 구성.

- 지역 전략 보고서(예: Alberta Esports Strategy)  
  - e스포츠 글로벌 매출(약 11억 달러 규모에서 2024년까지 16억 달러로 성장 전망), 전체 게임 시장(약 1,750억 → 2,180억 달러 전망) 같은 산업 규모 데이터를 제공합니다.[2]
  - LoL 2019 월즈 결승이 약 1억 명에 가까운 고유 시청자 수를 기록해 **같은 해 슈퍼볼을 상회했다**는 수치도 포함되어 있어, “최고 인기 이벤트 레벨에서는 e스포츠가 특정 전통 스포츠를 능가할 수 있다”는 정성적 논지를 뒷받침하는 데 유용합니다.[2]

- 국내·국제 공공 데이터 포털(작업 아이디어)  
  - 한국 통계청(KOSIS), 문화체육관광부, 국민체육진흥공단, 각국 스포츠 행정기관의 “스포츠 참여율, 관람률, 산업 매출” 통계를 수집해 전통 스포츠의 저변(참여율, 관람 경험)을 수량화합니다.  
  - 개별 포털에서 “스포츠 관람률”, “e스포츠 시청률/관람률” 같은 항목을 찾아, 연령대별·연도별로 추출해 CSV로 정리하면, Kaggle의 게임/e스포츠 데이터와 연계한 패널 분석이 가능해집니다.[8]

## “전통 스포츠에 필적하는가?”를 위한 지표 설계 예시

연구 질문을 데이터 분석 관점에서 정의하면 다음과 같이 나눌 수 있습니다.[1][3][2]

1. **최고 인기 이벤트 수준 비교**  
   - 지표: 단일 이벤트(월드컵 결승, 슈퍼볼, LoL Worlds, Dota2 TI)별 고유 시청자 수, 평균 동시 시청자, 상금 규모.  
   - 데이터 소스: WPI Sports vs Esports 연구 데이터(시청자 수) + Alberta 보고서(LoL Worlds, 상금)에 정리된 수치를 CSV로 재구성.[3][1][2]

2. **리그/시즌 단위 시청 추세**  
   - 지표: 연도별 평균 경기 시청자 수(전통 스포츠 리그 vs e스포츠 리그), 스트리밍 플랫폼별 시청 시간.  
   - 데이터 소스: WPI 연구에서 제시한 연도별 시청자 추세 + Kaggle “Video Game Trends / Streaming” 데이터에서 e스포츠 타이틀 시청 시간 추이.[4][1][3]

3. **산업 규모(매출·투자)**  
   - 지표: 글로벌·지역별 스포츠 산업 매출 vs e스포츠 매출, YoY 성장률.  
   - 데이터 소스: Alberta Esports Strategy(글로벌 e스포츠·게임 매출) + 각국 스포츠 산업 통계(문화부/체육부/경제 보고서 등)에서 수집.[2]

4. **세대별 선호도/관람률**  
   - 지표: 연령대별 전통 스포츠 vs e스포츠 시청 비율, 특히 Z세대·MZ세대.  
   - 데이터 소스: Escharts 등에서 제공하는 “Gen Z에서 e스포츠 시청이 전통 스포츠를 앞선다”는 분석, 각국 여론조사/설문 데이터를 공공 포털에서 추출해 CSV로 정리.[9]

이 지표들을 조합하여,  
- “절대 규모(관객 수·매출)”에서는 아직 전통 스포츠 우위지만,[1][2]
- “최고 이벤트 레벨”과 “젊은 세대 시청 선호”에서는 e스포츠가 상당 부분 필적하거나, 일부 종목을 상회한다는 식의 정량적 결론을 도출할 수 있습니다.[9][3][1][2]

## 실제 분석 워크플로우 예시

데이터 분석자로서 진행할 수 있는 실무 플로우를 한 번에 정리하면 다음과 같습니다.[5][6][4][3][1][2]

1. **데이터 수집·정리**
   - Kaggle에서 위 게임/스트리밍·산업 데이터셋들을 다운로드(csv).  
   - WPI “Sports vs Esports” 보고서, Alberta Esports Strategy에서 표·그래프 수치를 추출해 직접 CSV를 구성(예: `event_viewers.csv`, `industry_revenue.csv`).[3][1][2]
   - 공공 포털(예: KOSIS, 문화체육관광부)에서 스포츠 관람률·e스포츠 관람률 관련 연도별 통계 다운로드(엑셀→CSV 변환).

2. **데이터 모델링(관계 정의)**
   - 공통 키 생성: 연도(year), 국가(country), 이벤트 타입(type: sport/esport), 종목(league/title) 수준으로 조인 키를 정의.  
   - 예: `viewership_by_event`(전통 스포츠+e스포츠)와 `streaming_hours_by_title`(Kaggle)에서 e스포츠 타이틀 기준으로 매핑, 연도 기준으로 합산 후 비교.

3. **지표 생성**
   - 이벤트별 시청자 수, 평균 시청 시간, 이벤트 상금, 산업 매출, 연령대별 시청 비율 등 파생 변수 생성.  
   - z-score, index(전통 스포츠 평균 = 100, e스포츠 지수 계산) 등을 만들어 “필적성”을 정량화.

4. **시각화·해석**
   - Power BI나 Python으로  
     - 연도별 시청자 수/스트리밍 시간 추이,  
     - 이벤트별 시청자 TOP N 바 차트,  
     - 세대별 시청 비율 스택드 바/모자이크 등을 만들면 “어디까지 전통 스포츠에 근접했는지”를 직관적으로 보여줄 수 있습니다.

## 요약: 바로 써먹을 수 있는 데이터 출처 리스트

- Kaggle  
  - Video Game Trends / Streaming Data (e스포츠 게임 시청 추이 분석).[4]
  - Gaming Industry Trends (1000 Rows) (게임·e스포츠 타이틀 매출·행동 데이터).[6]
  - Top Games Dataset 🎮📊 (상위 인기 게임 중 e스포츠 타이틀 비중 분석).[7]
  - game dataset / steam_uncleaned.csv (장기 게임 관심도 패턴 분석).[5]

- 연구·보고서(직접 CSV 구성 필요)  
  - WPI “Sports versus Esports – A Comparison of Industry Size and Viewership” (전통 스포츠·e스포츠 이벤트 시청자 수, 산업 규모 비교).[1][3]
  - Alberta Esports Strategy Report (글로벌 e스포츠 매출, LoL Worlds vs 슈퍼볼 시청자 수, 투자 규모).[2]
  - Escharts 등 Gen Z 중심 e스포츠 시청 분석 기사 (세대별 선호 참고용).[9]

- 공공데이터(나라별 포털 활용)  
  - 스포츠 참여·관람률, e스포츠 관람률, 스포츠 산업 매출 통계(통계청, 문화체육관광부, OECD 등에서 Excel/CSV로 제공).[8]

이 정도 조합이면, “e스포츠의 대중적 인기가 어떤 조건/지표에서 전통 스포츠에 필적하는지”를 연도·세대·종목 단위로 꽤 정교하게 분석할 수 있습니다.

출처
[1] Sports versus Esports – A Comparison of Industry Size ... https://web.cs.wpi.edu/~claypool/papers/sports-esports-21/chapter-excerpt.pdf
[2] Alberta Esports Strategy https://www.calgaryeconomicdevelopment.com/assets/Reports/Sectors/Digital-Media-Entertainment/Alberta-Esports-Strategy-Report_FINAL_Aug22.pdf
[3] Sports vs Esports: http://web.cs.wpi.edu/~claypool/iqp/esports-18/report.pdf
[4] Video Game Trends Analysis with Streaming Data https://www.kaggle.com/code/erayaltay99/video-game-trends-analysis-with-streaming-data
[5] game dataset https://www.kaggle.com/datasets/utcurseyu/game-dataset
[6] Gaming Industry Trends (1000 Rows) https://www.kaggle.com/datasets/haseebindata/gaming-industry-trends-1000-rows
[7] Top Games Dataset 🎮📊 https://www.kaggle.com/datasets/waqi786/top-games-dataset
[8] Open government  Government at a Glance 2025 https://www.oecd.org/en/publications/government-at-a-glance-2025_0efd0bcd-en/full-report/open-government-data_619b668c.html
[9] Why Esports Viewership Is Outpacing Traditional Sports ... https://escharts.com/news/why-esports-viewership-outpacing-traditional-sports-among-gen-z
[10] Open access to high-value datasets: Government at a ... https://www.oecd.org/en/publications/government-at-a-glance-2025_0efd0bcd-en/full-report/open-access-to-high-value-datasets_6a8944a1.html
