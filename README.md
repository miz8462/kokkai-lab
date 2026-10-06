<!-- ~/projects/kokkai-lab/README.md -->
# kokkai-lab

国会会議録検索システムのデータを使った、国会発言のテキスト分析ツール。

国会の議論の中から**論点**を取り出し、「どの論点を、誰(議員/政府)が、どれくらい語っているか」を可視化する。「美しい日本の数字」の記事制作のための分析ツールで、アプリとして公開することは目的にしていない。

## 方針

* 発言者の「立場」を段落ごとに判定することはしない。立場は定義しだいで答えが変わる曖昧な概念で、AI・人間どちらのラベル付けでも一致率が安定しなかったため(経緯は `PROGRESS.md`)。
* 論点は、自分で候補を用意せず、議論の中から出てきた語だけで抽出する。論点が見えたら、その周辺の段落を読んで、論点内の対立や賛否を整理する。
* 論点の語群は定義として記事に明示する。
* 政府答弁は議員の発言と混ぜず、論点への「応答」として別枠で扱う。委員長報告は集計から除く。

## MVP

* **キーワード**:消費税
* **期間**:直近1年間
* **対象**:本会議
* **形態素解析**:SudachiPy
* **集計**:論点別の段落数、議員/政府の内訳、議員の発言者数、政党別の発言者数
* **可視化**:Nivo(サイト側)/ matplotlib・Plotly(分析中の確認用)
* **完了基準**:論点別のチャートを載せた記事を1本公開する

## Analysis Flow

```text
国会会議録API
    ↓ scripts/data/fetch_speeches.py
データ取得
    ↓ clean_speech.py / split_paragraphs.py / mark_roles.py
段落分割・役割付け(議員 / 政府 / 議長 / 委員長報告)
    ↓ scripts/analysis/find_issue_terms.py
論点の語の抽出(消費税の段落で際立つ語)
    ↓ data/issues/issue_groups.json
論点グループの定義
    ↓ scripts/analysis/issue_groups.py / issue_coverage.py
論点別の集計・網羅率の検査
    ↓ scripts/analysis/show_context.py
論点の周辺を読む(対立・賛否の整理)
    ↓
可視化 → 記事制作
```

## Tech Stack

* Python 3.12
* SudachiPy / SudachiDict-core
* pandas
* requests
* matplotlib / Plotly

## Directory

```text
scripts/data/      取得・前処理・役割付け
scripts/analysis/  論点の抽出・集計・文脈表示
scripts/plot/      分析中の確認用グラフ
data/interim/      paragraphs.csv, paragraphs_roles.csv
data/issues/       issue_groups.json(論点グループの語群)
data/labels/       立場ラベル付けの実験の記録(現在は使っていない)
output/            集計結果・文脈表示
```

## Roadmap

* [x] 環境構築
* [x] API疎通・データ取得
* [x] 前処理・段落分割
* [x] 役割付け(委員長報告の除外)
* [ ] 論点の抽出・語群の固め
* [ ] 論点ごとの周辺を読み、対立・賛否を整理
* [ ] 論点別のチャートをJSON化 → Nivoで実装
* [ ] 記事化

### Beyond MVP

1. Wordfish等のテキストスケーリング(ラベルを使わない方法)
2. 他のテーマへの展開(論点の抽出を同じ手順で行う)

### 見送ったもの

* 辞書ベースの感情・スタンス分析、BERTのファインチューニング: 段落単位の立場ラベルが安定しなかったため。