# 進行状態 (PROGRESS)

最終更新: 2026-09-25

## ファイル構成

```
kokkai-lab/
├── data/
│   ├── raw/          # 取得した生データ (gitignore対象)
│   └── interim/      # 中間ファイル(抽出・集計結果) (gitignore対象)
├── scripts/          # パイプライン(取得→前処理→集計)
│   ├── fetch_speeches.py
│   ├── extract_fields.py
│   ├── tokenize_speeches.py
│   ├── count_words.py
│   ├── aggregate.py
│   ├── clean_speech.py
│   ├── party_mapping.py
│   └── inspect_data.py
├── tests/            # 動作確認・検証
│   ├── verify_cleaning.py
│   └── verify_mapping.py
├── POLICY.md         # 分析方針
├── PROGRESS.md       # 進行状態
├── pyrightconfig.json
├── requirements.txt
└── .gitignore
```

実行例: `venv/bin/python scripts/count_words.py` (プロジェクト直下から)

## フェーズ1: 環境準備 ✅
- [x] Python 3.11系 / venv / requirements.txt
- [x] SudachiPy + SudachiDict-core 導入・動作確認 (`test_sudachi.py`)
- [x] requests / pandas / .gitignore / GitHubリポジトリ

## フェーズ2: API疎通 ✅
- [x] ドキュメント確認 / APIキー不要 / 疎通テスト (`test_api.py`)
- [x] JSONパース / ページネーション (maximumRecords=100, nextRecordPosition)
- [x] レートリミット配慮 (sleep 3秒) / エラー時挙動確認

## フェーズ3: データ取得 ✅
- [x] 条件確定 (直近1年・本会議・消費税)
- [x] `fetch_speeches.py` で全件取得 → `data/raw/speeches_20260925.json` (90件)

## フェーズ4: 前処理・集計 ✅
- [x] 会派→政党マッピング (`party_mapping.py`, `verify_mapping.py`)
- [x] ノイズ除去 (`clean_speech.py`, `verify_cleaning.py`)
- [x] フィールド抽出 (`extract_fields.py` → `data/interim/speeches_extracted.csv`)
- [x] Sudachi形態素解析＋品詞絞り込み (`tokenize_speeches.py` → `data/interim/tokens.csv`)
- [x] 頻出語カウント (`count_words.py` → `data/interim/word_freq.csv`)
- [x] 年別・政党別集計 (`aggregate.py` → `data/interim/speech_count_by_party.csv` ほか)
- [x] 中間ファイル保存 (`data/interim/`)

## フェーズ5: 可視化 ⬜
- [ ] ライブラリ選定 (matplotlib候補)
- [ ] 発言数推移 / 政党別比較 / 頻出語ランキング
- [ ] 記事の切り口メモ

## フェーズ6: サイト組み込み ⬜
- [ ] 既存記事構造確認 / 記事用JSON変換 / Nivoチャート選定
- [ ] 記事コンポーネント実装 / 出典注記 / ローカル確認
- [ ] Vercelデプロイ / Twitter発信