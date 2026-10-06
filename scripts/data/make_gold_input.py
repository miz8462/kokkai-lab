from pathlib import Path

import pandas as pd

GOLD = Path("data/labels/gold_sheet.csv")
LABELS = Path("data/labels/labels.csv")
OUT = Path("data/labels/gold_input.csv")

# 人間のラベルは使わず、speechIDとpara_idの組だけを取り出す
gold = pd.read_csv(GOLD, encoding="utf-8-sig")[["speechID", "para_id"]]
labels = pd.read_csv(LABELS, encoding="utf-8-sig")

cols = ["speechID", "para_id", "role", "text", "prev_text", "next_text"]
out = gold.merge(labels[cols], on=["speechID", "para_id"], how="left")
out.to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"{len(out)}件を {OUT} に書き出しました")