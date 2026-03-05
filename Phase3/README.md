# KDT 12th - Mini Project Phase 3: Esports Analysis

> Can Esports Be Recognized as a Sport?
> Data-driven analysis from three perspectives: Economic, Equality, and Medical.

## Project Structure

```
phase3/
├── README.md
│
├── 01_economic/          # Module A: Economic Analysis
│   ├── README.md
│   ├── initial/          # Initial analysis (Jupyter notebook)
│   ├── enhanced/         # Enhanced analysis with advanced visualizations
│   ├── final/            # Final consolidated analysis
│   └── final_output.zip
│
├── 02_equality/          # Module B: Equality / Market Comparison
│   ├── README.md
│   ├── initial/          # Initial analysis + crawling scripts
│   ├── enhanced_v1/      # First enhancement (Korean + English output)
│   ├── enhanced_v2/      # Second enhancement with deeper analysis
│   ├── final/            # Final consolidated analysis
│   └── final_output.zip
│
├── 03_medical/           # Module C: Medical / Physical Analysis
│   ├── README.md
│   ├── initial/          # Initial analysis (Jupyter notebook)
│   ├── enhanced_v1/      # First enhancement (sportiness analysis)
│   ├── enhanced_v2/      # Second enhancement (advanced metrics)
│   ├── final/            # Final consolidated analysis
│   └── final_output.zip
│
├── data/                 # All datasets
│   ├── raw/              # Uncompressed CSV files and dataset folders
│   ├── zip/              # Original Kaggle dataset archives (ZIP)
│   └── competition_structure/  # Esports competition structure analysis
│
├── presentation/         # Final deliverables
│   ├── esports_analysis.pptx       # Team presentation (PPTX)
│   ├── mini_project_team1.pdf      # Team presentation (PDF)
│   ├── 01_economic.pdf              # Module A report
│   ├── 02_equality.pdf              # Module B report
│   ├── 03_medical.pdf               # Module C report
│   ├── 01_README.md / 02_README.md / 03_README.md
│   └── 01~03_output_final.zip      # Output archives per module
│
├── reference/            # Reference materials & supplementary projects
│   ├── project_topic.pdf            # Project topic description
│   ├── kdt12_miniproject_topic.pdf  # KDT 12th mini-project guidelines
│   ├── kaggle_dataset.pdf           # Kaggle dataset documentation
│   ├── data_source_summary.pdf      # Data source references
│   ├── faker/            # Supplementary: Faker (esports player) analysis
│   │   ├── a_official_recognition/
│   │   ├── b_market_comparison/
│   │   ├── c_player_athletic/
│   │   └── d_dependency_analysis/
│   └── lol/              # Supplementary: LoL World Championship analysis
│
└── archive/              # Duplicate & original backup files
    ├── data.zip
    ├── esports_analysis_original.pptx
    ├── mini_project_team1_duplicate.pdf
    └── original_README.md
```

## Analysis Modules

### 01_economic - Economic Impact Analysis
- Prize money distribution and player earnings
- Market size and revenue prediction
- Lorenz curve and inequality metrics
- Growth trajectory analysis

### 02_equality - Esports vs Traditional Sports
- Market size and revenue structure comparison
- Viewership and sponsorship analysis
- Player earnings equity
- Twitch streaming data analysis
- Web crawling for popularity metrics

### 03_medical - Physical and Medical Analysis
- Player age distribution and peak performance age
- Heart rate and physical metrics comparison
- Cognitive load and reaction time analysis
- Sensor data analysis (IMU, EMG, GSR, EEG)
- Clustering analysis of player characteristics

## Datasets
- 24 datasets from Kaggle (see `data/zip/`)
- 10+ CSV files for direct analysis (see `data/raw/`)
- Esports sensor dataset with physiological measurements

## Module Folder Convention
Each module follows a consistent structure:
- `initial/` - First-pass analysis (Jupyter notebooks)
- `enhanced/` or `enhanced_v1/`, `enhanced_v2/` - Iterative improvements
- `final/` - Production-ready scripts and output
