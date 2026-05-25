
-- ============================================================
-- Create sentiment_scores table
-- ============================================================
CREATE TABLE sentiment_scores (
    id              INT IDENTITY(1,1) PRIMARY KEY,
    ticker          VARCHAR(10),
    total_mots      INT,
    mots_positifs   INT,
    mots_negatifs   INT,
    score_positif_pct DECIMAL(10,4),
    score_negatif_pct DECIMAL(10,4),
    score_net_pct   DECIMAL(10,4),
    sentiment       VARCHAR(20),
    date_analyse    DATETIME DEFAULT GETDATE()
);

-- ============================================================
-- Create top_words table
-- ============================================================
CREATE TABLE top_words (
    id           INT IDENTITY(1,1) PRIMARY KEY,
    ticker       VARCHAR(10),
    mot          VARCHAR(100),
    frequence    INT,
    type         VARCHAR(20),
    date_analyse DATETIME DEFAULT GETDATE()
);

-- ============================================================
-- Useful queries
-- ============================================================

-- Top sentiment scores
SELECT ticker, score_net_pct, sentiment
FROM sentiment_scores
ORDER BY score_net_pct DESC;

-- Top positive words per company
SELECT ticker, mot, frequence
FROM top_words
WHERE type = 'positif'
ORDER BY ticker, frequence DESC;

-- Top negative words per company
SELECT ticker, mot, frequence
FROM top_words
WHERE type = 'negatif'
ORDER BY ticker, frequence DESC;

-- Compare positive vs negative word counts
SELECT 
    ticker,
    SUM(CASE WHEN type = 'positif' THEN frequence ELSE 0 END) AS total_positif,
    SUM(CASE WHEN type = 'negatif' THEN frequence ELSE 0 END) AS total_negatif
FROM top_words
GROUP BY ticker
ORDER BY ticker;
