# scripts/data/mark_roles.py
#
# 【目的】
# paragraphs.csv の各段落に、発言者の種別(role)を付けた新しいCSVを作る。
# speakerPosition が入っているのは総理・大臣・議長だけで、委員長は空のため、
# 委員長報告(「質疑は、〜」「その詳細は会議録によって御承知願いたい」)が
# 「議員・自民党」の発言に混ざってしまう。これを分けるのが目的。
# role は 議員 / 政府 / 議長 / 委員長報告 の4種類。
# 委員長報告の判定は、報告の定型文に当たる段落を持つ発言者を特定して、
# その発言者の段落をまとめて「委員長報告」にする方式。
# 判定された発言者の全段落(冒頭40字)を画面に出すので、報告以外の質問が
# 混ざっていないかを目で確かめること。
#
# 【使い方】
# python scripts/data/mark_roles.py
#
# 【入力】 data/interim/paragraphs.csv
# 【出力】 data/interim/paragraphs_roles.csv(元のCSVは書き換えない)

import pandas as pd

INPUT = "data/interim/paragraphs.csv"
OUTPUT = "data/interim/paragraphs_roles.csv"
TEXT_COL = "text"
SPEAKER_COL = "speaker"
POSITION_COL = "speakerPosition"
CHAIR_PATTERN = r"^質疑は、|会議録によって御承知"

df = pd.read_csv(INPUT)
pos = df[POSITION_COL].fillna("").astype(str).str.strip()

chair_mask = df[TEXT_COL].str.contains(CHAIR_PATTERN, na=False, regex=True)
chair_speakers = sorted(df.loc[chair_mask, SPEAKER_COL].dropna().unique())

role = pd.Series("議員", index=df.index)
role[pos != ""] = "政府"
role[pos == "議長"] = "議長"
is_chair = df[SPEAKER_COL].isin(chair_speakers) & (pos == "")
role[is_chair] = "委員長報告"
df["role"] = role

df.to_csv(OUTPUT, index=False)

print(f"委員長報告と判定した発言者: {chair_speakers}")
print(df["role"].value_counts().to_string())
for s in chair_speakers:
    print(f"\n【{s}の全段落 {int((df[SPEAKER_COL] == s).sum())}件】")
    for _, r in df[df[SPEAKER_COL] == s].iterrows():
        print(f"- {r['role']} / {str(r[TEXT_COL])[:40]}")
print(f"\n{OUTPUT} に書き出しました")