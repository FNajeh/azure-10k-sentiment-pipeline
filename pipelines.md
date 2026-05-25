# ADF Pipelines Documentation

## Linked Services

| Name | Type | Description |
|------|------|-------------|
| `ls_adls_10k` | Azure Data Lake Storage Gen2 | Connects to `azure10kreportstkcmpt` |
| `ls_http_edgar` | HTTP | Base URL: `https://data.sec.gov` |
| `ls_databricks_10k` | Azure Databricks | Connects to `azure-10k-report-databricks` |
| `ls_azure_sql` | Azure SQL Database | Connects to `azure_db_10k_reports` |

## Pipeline 1 — pl_ingestion_10k_bronze

**Purpose**: Download 10-K metadata and reports from SEC EDGAR to Bronze layer.

**Activities**:
1. `ForEach` — Iterates over list of CIK numbers
   - Items: `@pipeline().parameters.tickers`
   - Inside: `Copy Activity` (HTTP → ADLS Bronze)

**Parameters**:
- `tickers` (Array): `["0000320193","0000789019","0001652044","0001326801","0001018724"]`

**Trigger**: `trigger_annuel_10k` — Annual schedule

**Flow**:
```
SEC EDGAR HTTP API
    ↓ Copy Activity (ForEach)
Bronze/10k/submissions/CIK{cik}.json
```

---

## Pipeline 2 — pl_transform_silver_gold

**Purpose**: Extract text, run sentiment analysis, load results to SQL.

**Activities**:
1. `Notebook` (`nb_sentiment_analysis`) — Runs Databricks notebook
   - Path: `/Workspace/Users/faissal8.najeh15@hotmail.com/nb_extract_10k`
2. `copy_gold_to_sql` — Copies sentiment scores CSV to SQL
   - Source: `ds_gold_csv` (Gold/sentiment/scores_sentiment_10k.csv)
   - Sink: `ds_sql_sentiment` (dbo.sentiment_scores)
3. `copy_words_to_sql` — Copies top words CSV to SQL
   - Source: `ds_gold_words` (Gold/sentiment/top_words_10k.csv)
   - Sink: `ds_sql_words` (dbo.top_words)

**Flow**:
```
Databricks Notebook
    ↓
Gold/sentiment/scores_sentiment_10k.csv → dbo.sentiment_scores
Gold/sentiment/top_words_10k.csv        → dbo.top_words
```

---

## Full Pipeline Chain

```
trigger_annuel_10k
    ↓
pl_ingestion_10k_bronze
    ↓ (Execute Pipeline)
pl_transform_silver_gold
    ├── Notebook (Databricks)
    ├── copy_gold_to_sql
    └── copy_words_to_sql
```
