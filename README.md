# kokkai-lab

国会会議録検索システムのデータを利用した、国会発言のテキスト分析ツール。

政党・議員の発言を収集・分析し、政策に関する発言傾向を可視化する。

## MVP

* **キーワード**：消費税
* **期間**：直近1年間
* **対象**：本会議
* **形態素解析**：SudachiPy
* **集計**：発言数・頻出語・政党別傾向
* **可視化**：matplotlib / Plotly
* **用途**：記事制作のための分析

## Analysis Flow

```text
国会会議録API
    ↓
データ取得
    ↓
前処理・形態素解析
    ↓
集計
    ↓
可視化
    ↓
記事制作
```

## Tech Stack

* Python 3.12
* SudachiPy / SudachiDict-core
* pandas
* requests
* matplotlib / Plotly

## Roadmap

* [x] 環境構築
* [x] API疎通・データ取得
* [x] 前処理・形態素解析
* [x] 政党別・年別集計
* [x] 可視化
* [ ] 記事化

### Beyond MVP

1. Wordfish等のテキストスケーリング
2. 辞書ベースの感情・スタンス分析
3. BERTファインチューニング
