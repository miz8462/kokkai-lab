"""
term_ablation.py — 語ごとの「外したときの影響」を出すスクリプト

目的:
  論点グループの各語について、
  - その語を含む段落数
  - 同じグループの中で、その語だけが支えている段落数
  - 全グループの中で、その語だけが支えている段落数(外すと網羅率が下がる数)
  - 他グループの語とも重なる段落数
  を出し、「外してよい語」「他と重なりすぎる語」を数字で判断できるようにする。

使い方:
  python scripts/analysis/term_ablation.py

入力:
  data/interim/paragraphs_roles.csv
  data/issues/issue_groups.json
出力:
  標準出力(グループ別の表)と output/term_ablation.csv
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PARAS = ROOT / "data/interim/paragraphs_clean.csv"
GROUPS = ROOT / "data/issues/issue_groups.json"
OUT = ROOT / "output/term_ablation.csv"


def load_groups(path):
    """JSONの形式(語のリスト / name+termsの辞書)のどちらでも読む"""
    raw = json.load(open(path, encoding="utf-8"))
    groups = {}
    for key, val in raw.items():
        if isinstance(val, dict):
            terms = val.get("terms") or val.get("words") or []
        else:
            terms = val
        groups[key] = terms
    return groups


df = pd.read_csv(PARAS)
df["exclude"] = df["exclude"].astype(str).str.lower().isin(["true", "1"])
has_kw = df["kw_extended"].astype(str).str.lower().isin(["true", "1"])
target = df[has_kw & (df["role"] != "委員長報告") & (~df["exclude"])]
texts = target["text"].fillna("")
print(f"対象: {len(target)}件")

groups = load_groups(GROUPS)

hit = {}
for gid, terms in groups.items():
    for t in terms:
        hit[(gid, t)] = texts.str.contains(t, regex=False)

total_terms = sum(hit.values())  # 段落ごとの、全グループでの一致語数
group_count = {
    gid: sum(hit[(gid, t)] for t in terms) for gid, terms in groups.items()
}

rows = []
for (gid, t), s in hit.items():
    rows.append({
        "論点": gid,
        "語": t,
        "該当": int(s.sum()),
        "グループ内でこの語だけ": int((s & (group_count[gid] == 1)).sum()),
        "全体でこの語だけ": int((s & (total_terms == 1)).sum()),
        "他グループにも入る": int((s & ((total_terms - group_count[gid]) > 0)).sum()),
    })

res = pd.DataFrame(rows)
OUT.parent.mkdir(exist_ok=True)
res.to_csv(OUT, index=False, encoding="utf-8-sig")
print(res.to_string(index=False))
print(f"\n{OUT} に書き出しました")
