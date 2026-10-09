# scripts/analysis/answer_blocks.py
#
# 【目的】
# 政府(role=政府)の段落を、「〜についてお尋ねがありました」などの見出し文で
# 答弁ブロックに区切り、論点グループごとに「答弁ブロック数」を数える。
# 段落数は定型答弁の繰り返しで膨らむため、「質問者ごとの答弁1回=1件」に近い
# 数え方で、政府の応答量を見るためのもの。
# 見出し文の取りこぼしや誤検出を確認するため、ブロックの一覧も出力する。
#
# 【使い方】
# python scripts/analysis/answer_blocks.py
#
# 【入力】 data/interim/paragraphs_clean.csv, data/issues/issue_groups.json
# 【出力】 output/answer_blocks.csv(ブロック一覧)
#          output/answer_blocks_summary.csv(論点別のブロック数)

import json
import re

import pandas as pd

INPUT = "data/interim/paragraphs_clean.csv"
GROUPS = "data/issues/issue_groups.json"
OUT_BLOCKS = "output/answer_blocks.csv"
OUT_SUMMARY = "output/answer_blocks_summary.csv"

HEADING = re.compile(r"お尋ね(が)?(あり|ござい)ました")
HEADING_MAX_LEN = 60

with open(GROUPS, encoding="utf-8") as f:
    groups = json.load(f)

df = pd.read_csv(INPUT)
for col in ["exclude", "kw_extended"]:
    df[col] = df[col].astype(str).str.lower().isin(["true", "1"])
df["text"] = df["text"].fillna("")

gov = df[df["role"] == "政府"].sort_values(["speechID", "para_id"]).copy()
gov["is_heading"] = gov["text"].map(
  lambda t: bool(HEADING.search(str(t))) and len(str(t)) < HEADING_MAX_LEN
)

# 同じ speechID の中で、見出し文が出るたびにブロック番号を進める
gov["block"] = gov.groupby("speechID")["is_heading"].cumsum()
gov["block_id"] = gov["speechID"] + "#" + gov["block"].astype(str)

# 対象段落(拡張語を含み、除外でない)を含むブロックだけ残す
target = gov[gov["kw_extended"] & (~gov["exclude"])]
rows = []
for name, words in groups.items():
    pattern = "|".join(words)
    hit = target[target["text"].str.contains(pattern, na=False, regex=True)]
    rows.append({
        "論点": name,
        "政府段落": len(hit),
        "答弁ブロック": hit["block_id"].nunique(),
    })

summary = pd.DataFrame(rows)
summary["段落/ブロック"] = (summary["政府段落"] / summary["答弁ブロック"]).round(2)
summary.to_csv(OUT_SUMMARY, index=False)

blocks = target.groupby("block_id").agg(
    date=("date", "first"),
    speaker=("speaker", "first"),
    段落数=("para_id", "count"),
    冒頭=("text", lambda s: s.iloc[0][:40]),
).reset_index()
blocks.to_csv(OUT_BLOCKS, index=False)

print(f"政府の見出し文: {int(gov['is_heading'].sum())}件")
print(summary.to_string(index=False))
print(f"{OUT_SUMMARY} と {OUT_BLOCKS} に書き出しました")