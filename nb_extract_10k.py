# Databricks notebook source
# Azure 10-K Sentiment Analysis Pipeline
# nb_extract_10k.py

# ============================================================
# CELL 1 — Install dependencies
# ============================================================
# %pip install azure-storage-file-datalake beautifulsoup4 lxml nltk

# ============================================================
# CELL 2 — Imports & Configuration
# ============================================================
from azure.storage.filedatalake import DataLakeServiceClient
from bs4 import BeautifulSoup
from collections import Counter
import json
import nltk
import pandas as pd
import re
import requests
import time

nltk.download('opinion_lexicon')
from nltk.corpus import opinion_lexicon

# Configuration
STORAGE_ACCOUNT = "azure10kreportstkcmpt"
STORAGE_KEY = "YOUR_STORAGE_KEY_HERE"  # Replace with your key

TICKERS = {
    "0000320193": "AAPL",
    "0000789019": "MSFT",
    "0001652044": "GOOGL",
    "0001326801": "META",
    "0001018724": "AMZN"
}

# Connect to Data Lake
service_client = DataLakeServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT}.dfs.core.windows.net",
    credential=STORAGE_KEY
)

bronze_client = service_client.get_file_system_client("bronze")
silver_client = service_client.get_file_system_client("silver")
gold_client   = service_client.get_file_system_client("gold")

positive_words = set(opinion_lexicon.positive())
negative_words = set(opinion_lexicon.negative())

print("✅ Configuration ready")

# ============================================================
# CELL 3 — Step 1: Fetch 10-K metadata from SEC EDGAR
# ============================================================
headers = {"User-Agent": "research-project contact@email.com"}

for cik in TICKERS:
    file_client = bronze_client.get_file_client(f"10k/submissions/CIK{cik}.json")
    data = json.loads(file_client.download_file().readall())

    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    accession_numbers = filings.get("accessionNumber", [])

    for i, form in enumerate(forms):
        if form == "10-K":
            acc = accession_numbers[i].replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{accession_numbers[i]}-index.htm"
            print(f"CIK {cik} → {url}")
            break

# ============================================================
# CELL 4 — Step 2: Download 10-K reports to Bronze
# ============================================================
for cik, ticker in TICKERS.items():
    file_client = bronze_client.get_file_client(f"10k/submissions/CIK{cik}.json")
    data = json.loads(file_client.download_file().readall())

    filings = data.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    accession_numbers = filings.get("accessionNumber", [])
    primary_documents = filings.get("primaryDocument", [])

    for i, form in enumerate(forms):
        if form == "10-K":
            acc = accession_numbers[i].replace("-", "")
            doc = primary_documents[i]
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{doc}"

            print(f"Downloading {ticker} → {url}")
            response = requests.get(url, headers=headers)

            out_client = bronze_client.get_file_client(f"10k/reports/CIK{cik}_10K.htm")
            out_client.upload_data(response.content, overwrite=True)
            print(f"✅ {ticker} saved to Bronze")

            time.sleep(0.5)
            break

# ============================================================
# CELL 5 — Step 3: Extract & clean text → Silver
# ============================================================
for cik, ticker in TICKERS.items():
    file_client = bronze_client.get_file_client(f"10k/reports/CIK{cik}_10K.htm")
    html_content = file_client.download_file().readall()

    soup = BeautifulSoup(html_content, "lxml")

    for tag in soup(["script", "style", "table"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    clean_text = "\n".join(lines)

    out_client = silver_client.get_file_client(f"10k/{ticker}_10K_clean.txt")
    out_client.upload_data(clean_text.encode("utf-8"), overwrite=True)
    print(f"✅ {ticker} → {len(clean_text)} chars saved to Silver")

# ============================================================
# CELL 6 — Step 4: Sentiment analysis → Gold
# ============================================================
results = []

for cik, ticker in TICKERS.items():
    file_client = silver_client.get_file_client(f"10k/{ticker}_10K_clean.txt")
    text = file_client.download_file().readall().decode("utf-8").lower()

    words = re.findall(r'\b[a-z]+\b', text)
    total_words = len(words)

    pos_count = sum(1 for w in words if w in positive_words)
    neg_count = sum(1 for w in words if w in negative_words)

    pos_score = round(pos_count / total_words * 100, 4)
    neg_score = round(neg_count / total_words * 100, 4)
    net_score = round(pos_score - neg_score, 4)
    label = "POSITIF" if net_score > 0 else "NÉGATIF"

    results.append({
        "ticker": ticker,
        "total_mots": total_words,
        "mots_positifs": pos_count,
        "mots_negatifs": neg_count,
        "score_positif_pct": pos_score,
        "score_negatif_pct": neg_score,
        "score_net_pct": net_score,
        "sentiment": label
    })

    print(f"✅ {ticker} → net: {net_score}% ({label})")

df_results = pd.DataFrame(results)

# ============================================================
# CELL 7 — Step 5: Top words analysis → Gold
# ============================================================
word_freq_results = []

for cik, ticker in TICKERS.items():
    file_client = silver_client.get_file_client(f"10k/{ticker}_10K_clean.txt")
    text = file_client.download_file().readall().decode("utf-8").lower()

    words = re.findall(r'\b[a-z]+\b', text)

    pos_found = [w for w in words if w in positive_words]
    neg_found = [w for w in words if w in negative_words]

    for word, count in Counter(pos_found).most_common(10):
        word_freq_results.append({"ticker": ticker, "mot": word, "frequence": count, "type": "positif"})

    for word, count in Counter(neg_found).most_common(10):
        word_freq_results.append({"ticker": ticker, "mot": word, "frequence": count, "type": "negatif"})

df_words = pd.DataFrame(word_freq_results)

# ============================================================
# CELL 8 — Step 6: Save results to Gold
# ============================================================
# Rename columns
df_results = df_results.rename(columns={
    "score_positif_%": "score_positif_pct",
    "score_negatif_%": "score_negatif_pct",
    "score_net_%": "score_net_pct"
})

# Save sentiment scores
csv_data = df_results.to_csv(index=False)
out_client = gold_client.get_file_client("sentiment/scores_sentiment_10k.csv")
out_client.upload_data(csv_data.encode("utf-8"), overwrite=True)
print("✅ Sentiment scores saved to Gold")

# Save top words
csv_words = df_words.to_csv(index=False)
out_client2 = gold_client.get_file_client("sentiment/top_words_10k.csv")
out_client2.upload_data(csv_words.encode("utf-8"), overwrite=True)
print("✅ Top words saved to Gold")

# Save JSON
json_data = df_results.to_json(orient="records", indent=2)
out_client3 = gold_client.get_file_client("sentiment/scores_sentiment_10k.json")
out_client3.upload_data(json_data.encode("utf-8"), overwrite=True)
print("✅ JSON saved to Gold")
