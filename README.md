# Azure 10-K Sentiment Analysis Pipeline

A complete data pipeline for sentiment analysis of SEC 10-K annual reports using Azure Data Factory, Databricks, and Power BI.

## Architecture

```
SEC EDGAR API
    ↓
Azure Data Factory (Orchestration)
    ↓
Azure Data Lake Gen2 (Medallion Architecture)
    ├── Bronze  → Raw 10-K reports (HTML/JSON)
    ├── Silver  → Cleaned text
    └── Gold    → Sentiment scores + Top words
    ↓
Azure SQL Database
    ├── sentiment_scores
    └── top_words
    ↓
Power BI Dashboard
```

## Companies Analyzed

| Ticker | CIK        |
|--------|------------|
| AAPL   | 0000320193 |
| MSFT   | 0000789019 |
| GOOGL  | 0001652044 |
| META   | 0001326801 |
| AMZN   | 0001018724 |

## Azure Resources

| Resource | Name |
|----------|------|
| Resource Group | Azure-10k-report-njh |
| Storage Account | azure10kreportstkcmpt |
| Data Factory | azure-10k-report-datafactory |
| Databricks Workspace | azure-10k-report-databricks |
| SQL Server | azureserver10kreports |
| SQL Database | azure_db_10k_reports |

## Project Structure

```
├── notebooks/
│   └── nb_extract_10k.py        # Main Databricks notebook
├── sql/
│   ├── create_sentiment_scores.sql
│   └── create_top_words.sql
├── adf/
│   └── pipelines.md             # ADF pipeline documentation
├── powerbi/
│   └── dashboard.md             # Power BI dashboard documentation
├── docs/
│   └── setup.md                 # Setup guide
└── README.md
```

## Pipeline Steps

### Pipeline 1 — Ingestion (ADF)
- Fetches 10-K metadata from SEC EDGAR API
- Downloads full 10-K reports (HTM format)
- Stores raw files in Bronze layer

### Pipeline 2 — Transform (ADF → Databricks)
- Extracts clean text from HTML reports (BeautifulSoup)
- Stores cleaned text in Silver layer
- Runs sentiment analysis using NLTK opinion lexicon
- Saves scores and top words to Gold layer (CSV)
- Copies results to Azure SQL Database

## Sentiment Analysis

Uses the **NLTK Opinion Lexicon** with:
- 2,006 positive words
- 4,783 negative words

**Output metrics per company:**
- `total_mots` — Total word count
- `mots_positifs` — Positive word count
- `mots_negatifs` — Negative word count
- `score_positif_pct` — Positive word percentage
- `score_negatif_pct` — Negative word percentage
- `score_net_pct` — Net sentiment score
- `sentiment` — POSITIF / NÉGATIF label

## Results (Latest Run)

| Ticker | Score Net | Sentiment |
|--------|-----------|-----------|
| AAPL   | 0.1051%   | POSITIF   |
| MSFT   | 0.3216%   | POSITIF   |
| GOOGL  | 0.1996%   | POSITIF   |
| META   | 0.0481%   | POSITIF   |
| AMZN   | 0.6380%   | POSITIF   |

## Setup

See [docs/setup.md](docs/setup.md) for full setup instructions.

## Tech Stack

- **Orchestration**: Azure Data Factory
- **Storage**: Azure Data Lake Storage Gen2
- **Compute**: Azure Databricks (Serverless)
- **Database**: Azure SQL Database
- **Visualization**: Power BI
- **Language**: Python 3.12
- **Libraries**: BeautifulSoup, NLTK, pandas, azure-storage-file-datalake
