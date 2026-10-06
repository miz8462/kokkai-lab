<!-- ~/projects/kokkai-lab/PROGRESS.md -->
# 進行状態 (PROGRESS)

最終更新: 2026-10-06

## ファイル構成

```
kokkai-lab/
├── data/
│   ├── raw/          # 取得した生データ (gitignore対象)
│   ├── interim/      # 中間ファイル (paragraphs.csv, paragraphs_roles.csv など)
│   ├── issues/       # issue_groups.json (論点グループの語群)
│   └── labels/       # 立場ラベル付けの実験の記録 (現在は使っていない)
├── scripts/
│   ├── data/         # 取得・前処理・役割付け
│   ├── analysis/     # 論点の抽出・集計・文脈表示
│   └── plot/         # 分析中の確認用グラフ
├── output/           # 集計結果・文脈表示
├── tests/            # 動作確認・検証
├── POLICY.md         # 分析方針
├── PROGRESS.md       # 進行状態
├── pyrightconfig.json
├── requirements.txt
└── .gitignore
```

実行例: `venv/bin/python scripts/analysis/issue_groups.py` (プロジェクト直下から)

## フェーズ1: 環境準備 ✅
- [x] Python 3.12 / venv / requirements.txt
- [x] SudachiPy + SudachiDict-core 導入・動作確認
- [x] requests / pandas / .gitignore / GitHubリポジトリ

## フェーズ2: API疎通 ✅
- [x] ドキュメント確認 / APIキー不要 / 疎通テスト
- [x] JSONパース / ページネーション (maximumRecords=100, nextRecordPosition)
- [x] レートリミット配慮 (sleep 3秒) / エラー時挙動確認

## フェーズ3: データ取得 ✅
- [x] 条件確定 (直近1年・本会議・消費税)
- [x] `fetch_speeches.py` で全件取得 (90件)

## フェーズ4: 前処理 ✅
- [x] 会派→政党マッピング / ノイズ除去 / フィールド抽出
- [x] Sudachi形態素解析・頻出語カウント・年別/政党別集計
- [x] 段落分割 `split_paragraphs.py` → `data/interim/paragraphs.csv` (全4185段落、消費税を含む258段落)
- [x] 役割付け `mark_roles.py` → `data/interim/paragraphs_roles.csv`
  (議員 / 政府 / 議長 / 委員長報告。委員長の藤川政人の19段落は報告のみなので除外。消費税を含む対象は255段落)

## フェーズ5: 立場ラベル付けの実験 ⛔ 中止(経緯の記録)
- 「政党×立場」のチャートを目指して、議員154段落に stance(a〜e)・topics を付ける計画だった。
- gold 30段落で、AIと人間の立場の一致率は v0 80% → v1 53% → v2 83.3% (κ約0.68)。ただし、定義を調整するたびに結果が動いただけで、モデルの出来ではなかった。
- 新しい30段落 (gold2) では、v2の一致率が60.0% (18/30)。食い違い12件のうち9件は、人間e(該当なし)でAIa(減税・廃止)。
- 原因は手法ではなく問題設定にあると判断した。国会では減税が前提で質問が組まれて明示的な要求が少なく、暗示を拾えば定義依存が戻り、明示だけにすると数字が立たない。「立場」は、車や人の判別と違って、正解が段落の中に1つ決まっていない。
- 方針転換: 立場の判定をやめ、論点を抽出する方式に切り替えた。
- `data/labels/` と `scripts/data/*label*`、`scripts/analysis/compare_labels.py` などは記録として残す。

## フェーズ5(新): 論点の抽出 🔄 作業中
方針: 論点は自分で候補を用意せず、議論の中から出た語だけで抽出する。
- [x] `find_issue_terms.py`: 消費税の段落で際立つ語を統計で抽出
- [x] `show_context.py`: 語の周辺を前後の段落つきで出力
- [x] `term_spread.py`: 語が特定の発言者に偏っていないかを確認
- [x] `data/issues/issue_groups.json`: 論点グループ(A〜N)の語群を定義
- [x] `issue_groups.py` / `issue_coverage.py`: 論点別の集計・網羅率・未分類の段落
- [ ] 更新した語群での結果を読み、一般的すぎる語を外す
- [ ] 未分類の段落に、残っている論点がないかを見る

## フェーズ6: 論点の周辺を読む ⬜
- [ ] 広い論点(食料品の範囲、給付つき税額控除、事業者の負担)から、該当段落を議員と政府を対にして読む
- [ ] 論点内の対立・賛否を整理する
- [ ] 論点別の「議員の問い量 vs 政府の答弁量」を、記事の軸にできるか検討する
- [ ] 政府の同じ答弁(失われた三十年は消費税だけでは論じられない、など)の引用候補

## フェーズ7: サイト組み込み ⬜
- [ ] 記事用JSON変換(出典・語群の定義・少数の注記つき)
- [ ] Nivoチャート選定・記事コンポーネント実装・ローカル確認
- [ ] Vercelデプロイ / 記事執筆 / X発信

## 決めたこと
- 政府答弁は、政党の発言と混ぜず、論点への応答として別枠にする。
-