[setup.md](https://github.com/user-attachments/files/28221147/setup.md)

# Setup Guide — Azure 10-K Sentiment Pipeline

## Prerequisites

- Azure subscription (Pay-as-you-go or Free tier)
- Azure CLI installed
- Power BI Desktop installed
- GitHub account

---

## Step 1 — Create Resource Group

```bash
az login

az group create \
  --name Azure-10k-report-njh \
  --location francecentral
```

---

## Step 2 — Create Data Lake Storage Gen2

```bash
az storage account create \
  --name azure10kreportstkcmpt \
  --resource-group Azure-10k-report-njh \
  --location francecentral \
  --sku Standard_LRS \
  --kind StorageV2 \
  --hierarchical-namespace true

# Create containers
az storage fs create -n bronze --account-name azure10kreportstkcmpt --auth-mode login
az storage fs create -n silver --account-name azure10kreportstkcmpt --auth-mode login
az storage fs create -n gold   --account-name azure10kreportstkcmpt --auth-mode login
```

---

## Step 3 — Create Azure Data Factory

```bash
az datafactory create \
  --name azure-10k-report-datafactory \
  --resource-group Azure-10k-report-njh \
  --location francecentral
```

---

## Step 4 — Create Azure Databricks

```bash
az databricks workspace create \
  --name azure-10k-report-databricks \
  --resource-group Azure-10k-report-njh \
  --location francecentral \
  --sku premium
```

---

## Step 5 — Create Azure SQL Database

```bash
az sql server create \
  --name azureserver10kreports \
  --resource-group Azure-10k-report-njh \
  --location francecentral \
  --admin-user sqladmin \
  --admin-password YOUR_PASSWORD

az sql db create \
  --name azure_db_10k_reports \
  --server azureserver10kreports \
  --resource-group Azure-10k-report-njh \
  --edition GeneralPurpose \
  --compute-model Serverless \
  --family Gen5 \
  --capacity 1
```

---

## Step 6 — Configure ADF Linked Services

In ADF Studio → Manage → Linked Services → create:

1. **ls_adls_10k** — Azure Data Lake Storage Gen2
   - Storage account: `azure10kreportstkcmpt`
   - Auth: Account Key

2. **ls_http_edgar** — HTTP
   - Base URL: `https://data.sec.gov`
   - Auth: Anonymous

3. **ls_databricks_10k** — Azure Databricks
   - Workspace URL: `https://adb-XXXX.azuredatabricks.net`
   - Access token: Generate PAT in Databricks
   - Cluster: Serverless

4. **ls_azure_sql** — Azure SQL Database
   - Server: `azureserver10kreports.database.windows.net`
   - Database: `azure_db_10k_reports`
   - Auth: SQL Authentication

---

## Step 7 — Create SQL Tables

Run `sql/create_tables.sql` in Azure SQL Query Editor.

---

## Step 8 — Upload Notebook to Databricks

Upload `notebooks/nb_extract_10k.py` to Databricks workspace.
Update `STORAGE_KEY` with your actual storage account key.

---

## Step 9 — Create ADF Pipelines

Follow `adf/pipelines.md` to configure:
- `pl_ingestion_10k_bronze`
- `pl_transform_silver_gold`

---

## Step 10 — Connect Power BI

1. Open Power BI Desktop
2. Get Data → Azure SQL Database
3. Server: `azureserver10kreports.database.windows.net`
4. Database: `azure_db_10k_reports`
5. Load tables: `sentiment_scores`, `top_words`
6. Create visuals

---

## Security Notes

- Never commit `STORAGE_KEY` or passwords to GitHub
- Use Azure Key Vault for secrets in production
- Use Managed Identity instead of Account Key when possible
