# scripts/analysis/issue_groups.py
#
# 【目的】
# data/issues/issue_groups.json で定義した論点グループごとに、
# 「消費税」を含む段落(委員長報告を除く)での広がりを集計する。
# グループのいずれかの語を含む段落を、そのグループの段落とみなす。
# 出すもの: 段落数、議員段落/政府段落、議員の発言者数、議員の最多発言者と割合、
#           政党別の発言者数(段落数ではなく人数)。
# 記事のチャートの元データになる。語の組み分けは自分で決めた定義なので、
# 記事では語群をそのまま明示する。
#
# 【使い方】
# python scripts/analysis/issue_groups.py
#
# 【入力】 data/interim/paragraphs_roles.csv, data/issues/issue_groups.json
# 【出力】 output/issue_groups.csv(画面にも表示)

import json

import pandas as pd

INPUT = "data/interim/paragraphs_roles.csv"
GROUPS = "data/issues/issue_groups.json"
OUTPUT = "output/issue_groups.csv"
TEXT_COL = "text"
SPEAKER_COL = "speaker"
PARTY_COL = "party"
KEYWORD = "消費税"

with open(GROUPS, encoding="utf-8") as f:
    groups = json.load(f)

df = pd.read_csv(INPUT)
df = df[df[TEXT_COL].str.contains(KEYWORD, na=False) & (df["role"] != "委員長報告")].copy()

rows = []
for name, words in groups.items():
    pattern = "|".join(words)
    sub = df[df[TEXT_COL].str.contains(pattern, na=False, regex=True)]
    mem = sub[sub["role"] == "議員"]
    top = mem[SPEAKER_COL].value_counts()
    by_party = mem.groupby(PARTY_COL)[SPEAKER_COL].nunique().sort_values(ascending=False)
    rows.append({
        "論点": name,
        "段落": len(sub),
        "議員段落": len(mem),
        "政府段落": int((sub["role"] == "政府").sum()),
        "議員の発言者": mem[SPEAKER_COL].nunique(),
        "議員の最多": top.index[0] if len(top) else "",
        "最多の割合": round(top.iloc[0] / len(mem), 2) if len(top) else 0,
        "政党別の発言者数": " ".join(f"{p}{n}" for p, n in by_party.items()),
    })

res = pd.DataFrame(rows)
res.to_csv(OUTPUT, index=False)
print(f"対象: 消費税を含む段落(委員長報告を除く) {len(df)}件")
print(res.to_string(index=False))
