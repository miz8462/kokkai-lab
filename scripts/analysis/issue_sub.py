"""
issue_sub.py — 論点のサブグループ別に、議員・政府の段落数と政党別の発言者数を出すスクリプト

目的:
  issue_A_sub.json のような「サブ論点の語群」を読み、サブ論点ごとに
  段落数・議員/政府の内訳・議員の発言者数・政党別の発言者数を出す。
  特に A2(食料品だけか一律か)で、どの政党がどの立場の語を使うかを見る。

使い方:
  python scripts/analysis/issue_sub.py data/issues/issue_A_sub.json

入力:
  data/interim/paragraphs_clean.csv, 引数で指定したJSON
出力:
  標準出力と output/issue_sub.csv
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PARAS = ROOT / "data/interim/paragraphs_clean.csv"
OUT = ROOT / "output/issue_sub.csv"

groups = json.load(open(sys.argv[1], encoding="utf-8"))

df = pd.read_csv(PARAS)
df["exclude"] = df["exclude"].astype(str).str.lower().isin(["true", "1"])
df["text"] = df["text"].fillna("")
df["party"] = df["party"].fillna("")
has_kw = df["kw_extended"].astype(str).str.lower().isin(["true", "1"])
df = df[has_kw & (df["role"] != "委員長報告") & (~df["exclude"])].copy()
print(f"対象: {len(df)}件")

rows = []
for name, terms in groups.items():
    hit = df["text"].apply(lambda s: any(t in s for t in terms))
    sub = df[hit]
    mem = sub[sub["role"] == "議員"]
    top = mem["speaker"].value_counts()
    party_n = mem.groupby("party")["speaker"].nunique().sort_values(ascending=False)
    rows.append({
        "サブ論点": name,
        "段落": len(sub),
        "議員段落": len(mem),
        "政府段落": int((sub["role"] == "政府").sum()),
        "議員の発言者": mem["speaker"].nunique(),
        "議員の最多": top.index[0] if len(top) else "",
        "最多の割合": round(top.iloc[0] / len(mem), 2) if len(mem) else 0,
        "政党別の発言者数": " ".join(f"{p}{n}" for p, n in party_n.items()),
    })

res = pd.DataFrame(rows)
OUT.parent.mkdir(exist_ok=True)
res.to_csv(OUT, index=False, encoding="utf-8-sig")
print(res.to_string(index=False))
print(f"\n{OUT} に書き出しました")
