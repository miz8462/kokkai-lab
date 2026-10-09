from pathlib import Path

import pandas as pd

GOLD1 = Path("data/labels/gold_sheet.csv")
LABELS = Path("data/labels/labels.csv")
OUT = Path("data/labels/gold2_sheet.csv")

if OUT.exists():
    raise SystemExit(f"{OUT} は既にあります。手作業のラベルを守るため、中止します。")

used = pd.read_csv(GOLD1, encoding="utf-8-sig")[["speechID", "para_id"]]
labels = pd.read_csv(LABELS, encoding="utf-8-sig")

# 議員の段落のうち、1回目の30件を除いたものから30件を無作為に抽出
members = labels[labels["role"] == "議員"]
merged = members.merge(used, on=["speechID", "para_id"], how="left", indicator=True)
candidates = merged[merged["_merge"] == "left_only"]
sample = candidates.sample(n=30, random_state=7).sort_values(["speechID", "para_id"])

cols = ["speechID", "para_id", "text", "prev_text", "next_text", "stance", "note"]
sample[cols].to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"{len(sample)}件を {OUT} に書き出しました")
