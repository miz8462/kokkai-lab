from pathlib import Path

import pandas as pd

OUT = Path("data/labels/gold_sheet.csv")

if OUT.exists():
    raise SystemExit(f"{OUT} は既にあります。手作業のラベルを守るため、中止します。")

df = pd.read_csv("data/labels/labels.csv")
members = df[df["role"] == "議員"]

# 30段落を無作為に抽出(random_stateを固定して、再現できるようにする)
sample = members.sample(n=30, random_state=42).sort_values(["speechID", "para_id"])

cols = ["speechID", "para_id", "text", "prev_text", "next_text", "topics", "stance", "note"]
sample[cols].to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"{len(sample)}件を {OUT} に書き出しました")
