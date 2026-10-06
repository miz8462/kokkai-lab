# タスク
国会会議録の段落に、論点と立場のラベルを付けてください。

<!--# 入力
- `data/labels/labels.csv`(読み取り専用)
- 今回の対象は、`role`列が「議員」の段落だけです
- 使う列は `speechID`, `para_id`, `role`, `text`, `prev_text`, `next_text` のみです
- `party`, `speaker`, `topics`, `stance`, `note` の列は、判断に使わないでください
 -->
# 入力(試験用)
- `data/labels/gold_input.csv`(30件、全件が対象です)
- 使う列は `speechID`, `para_id`, `text`, `prev_text`, `next_text` のみです
- 他のCSVは読まないでください(`gold_sheet.csv` と `labels.csv` を含む)

# ラベルの定義
`data/labels/LABEL_GUIDE.md` を最初に読み、その定義と判断ルールを厳守してください。

<!--# 出力
`data/labels/ai_labels.csv` に、次の列で書き出してください(UTF-8、1行目はヘッダー)。-->

# 出力(試験用)
`data/labels/ai_labels_v2_gold.csv`(列は今までと同じ)


speechID,para_id,ai_stance,ai_topics,ai_confidence,ai_note

- `ai_stance` は、この段落・前の段落・次の段落のいずれかに根拠となる語句がある場合だけ a〜d を付け、どこにも根拠がなければ「e」にしてください
- `ai_topics`: LABEL_GUIDEの入力コード(f〜m)。最大2つまで。複数ならセミコロン(;)区切り。内容のないつなぎの一文は「m」
- `ai_confidence`: 高 / 中 / 低 のいずれか
- `ai_note` には、根拠にした語句を短く引用し、どの段落のものか(本文/前/次)を書いてください。カンマ(,)は使わないでください

# 判断の原則
- 判断の根拠は `text` の内容だけにしてください。`prev_text` と `next_text` は、文脈を確認するための参考です
- 政党名や話者の評判から立場を推測しないでください(`party` は見ない前提です)
- 迷ったら、無理に決めず、`ai_stance` を「条件付き・不明確」、`ai_confidence` を「低」にしてください
- 質問の形でも、前提に主張があれば主張として扱い、検討を尋ねるだけなら「該当なし」にしてください(LABEL_GUIDEの判断ルールどおり)

# 作業手順
1. 対象の段落を、20件ずつのバッチで処理します
2. 各バッチが終わるたびに、`ai_labels.csv` に追記します(ヘッダーは最初の1回だけ)
3. 既に `ai_labels.csv` にある `speechID` と `para_id` の組はスキップしてください(中断しても再開できるようにするためです)
4. 処理した件数のみ(ラベルの内訳や内容は報告しないでください)

# してはいけないこと
- `labels.csv` を編集する
- `labels.csv` の `topics`, `stance`, `note` 列の内容を読み取って、参考にする
- 上記以外のファイルを変更・作成する
- ターミナルでコマンドを実行する(件数の確認も、ファイルを読んで行う)

# 完了時の報告
- 処理した件数
- `ai_stance` ごとの件数
- `ai_confidence` が「低」の件数
