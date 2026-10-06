# scripts/analysis/term_spread.py
#
# 【目的】
# 論点の候補になった語が、特定の1人の発言に偏っていないかを調べる。
# 指定した語ごとに、「消費税」を含む段落での出現段落数・発言数・発言者数・
# 議員/政府の内訳・議員の最多発言者とその割合・議員の政党別の内訳を出す。
# 委員長報告(role=委員長報告)は集計から除く。
# 段落数が多くても1人の長い発言から出ているだけの語は、論点の大きさを
# 過大に見せるので、それを見分けるために使う。
#
# 【使い方】
# python scripts/analysis/term_spread.py 滞納 倒産 担税力
#
# 【入力】 data/interim/paragraphs_roles.csv(scripts/data/mark_roles.py の出力)
# 【出力】 output/term_spread.csv(画面にも同じ表を表示)

import sys

import pandas as pd

INPUT = "data/interim/paragraphs_roles.csv"
TEXT_COL = "text"
SPEECH_COL = "speechID"
SPEAKER_COL = "speaker"
PARTY_COL = "party"
KEYWORD = "消費税"
OUTPUT = "output/term_spread.csv"

terms = sys.argv[1:]
if not terms:
    raise SystemExit("語を引数で渡してください。例: python scripts/analysis/term_spread.py 滞納 倒産")

df = pd.read_csv(INPUT)
df = df[df[TEXT_COL].str.contains(KEYWORD, na=False) & (df["role"] != "委員長報告")].copy()

rows = []
for t in terms:
    sub = df[df[TEXT_COL].str.contains(t, na=False)]
    if len(sub) == 0:
        rows.append({"term": t, "段落": 0})
        continue
    mem = sub[sub["role"] == "議員"]
    top = mem[SPEAKER_COL].value_counts()
    parties = mem[PARTY_COL].value_counts()
    rows.append({
        "term": t,
        "段落": len(sub),
        "発言": sub[SPEECH_COL].nunique(),
        "議員段落": len(mem),
        "議員の発言者": mem[SPEAKER_COL].nunique(),
        "政府段落": int((sub["role"] == "政府").sum()),
        "議員の最多": top.index[0] if len(top) else "",
        "最多の割合": round(top.iloc[0] / len(mem), 2) if len(top) else 0,
        "議員の政党": " ".join(f"{p}{n}" for p, n in parties.items()),
    })

res = pd.DataFrame(rows)
res.to_csv(OUTPUT, index=False)
print(res.to_string(index=False))