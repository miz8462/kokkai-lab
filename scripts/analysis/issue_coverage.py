# scripts/analysis/issue_coverage.py
#
# 【目的】
# data/issues/issue_groups.json の語群が、うまく機能しているかを検査する。
# (1) 語ごとの該当段落数を出す。一般的すぎる語(多くの無関係な段落を拾う語)を
#     見つけるため。
# (2) どのグループにも入らなかった段落を、政党・役職つきで output/uncovered.md に
#     書き出す。語群が見落とした論点を探すための材料になる。
# (3) グループに入った段落数と、入らなかった段落数の割合を出す。
#
# 【使い方】
# python scripts/analysis/issue_coverage.py
#
# 【入力】 data/interim/paragraphs_roles.csv, data/issues/issue_groups.json
# 【出力】 output/uncovered.md(未分類の段落一覧)、画面に語別の件数と網羅率

import json

import pandas as pd

INPUT = "data/interim/paragraphs_roles.csv"
GROUPS = "data/issues/issue_groups.json"
OUTPUT = "output/uncovered.md"
TEXT_COL = "text"
PARTY_COL = "party"
KEYWORD = "消費税"

with open(GROUPS, encoding="utf-8") as f:
    groups = json.load(f)

df = pd.read_csv(INPUT)
df = df[df[TEXT_COL].str.contains(KEYWORD, na=False) & (df["role"] != "委員長報告")].copy()

print("【語ごとの該当段落数】")
all_words = []
for name, words in groups.items():
    counts = {w: int(df[TEXT_COL].str.contains(w, na=False).sum()) for w in words}
    print(f"{name}: " + " / ".join(f"{w}{n}" for w, n in counts.items()))
    all_words += words

pattern = "|".join(all_words)
covered = df[TEXT_COL].str.contains(pattern, na=False, regex=True)
print(f"\n【網羅率】グループのどれかに入った段落: {int(covered.sum())} / {len(df)}")

rest = df[~covered]
lines = [f"# 未分類の段落: {len(rest)}件\n"]
for _, r in rest.iterrows():
    who = r[PARTY_COL] if r["role"] == "議員" else r["role"]
    lines.append(f"- [{who}] {str(r[TEXT_COL]).replace(chr(10), ' ')}\n")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"未分類の段落 {len(rest)}件を {OUTPUT} に書き出しました")
