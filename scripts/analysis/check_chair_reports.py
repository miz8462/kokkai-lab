# scripts/analysis/check_chair_reports.py
#
# 【目的】
# 委員長報告(「質疑は、〜」「その詳細は会議録によって御承知願いたい」など)が、
# paragraphs.csv の中で「議員」「自民党」として扱われていないかを調べる。
# speakerPosition の値の一覧と、委員長報告らしい段落の発言者・役職・冒頭を出す。
# 除外ルールを決めるための調査用で、データは書き換えない。
#
# 【使い方】
# python scripts/analysis/check_chair_reports.py
#
# 【入力】 data/interim/paragraphs.csv
# 【出力】 画面表示のみ

import pandas as pd

INPUT = "data/interim/paragraphs.csv"
TEXT_COL = "text"
SPEAKER_COL = "speaker"
POSITION_COL = "speakerPosition"
PARTY_COL = "party"

df = pd.read_csv(INPUT)

print("【speakerPosition の値(件数)】")
print(df[POSITION_COL].fillna("(空)").value_counts().head(30).to_string())

mask = df[TEXT_COL].str.contains("会議録によって御承知|^質疑は|質疑は、", na=False, regex=True)
sub = df[mask]
print(f"\n【委員長報告らしい段落: {len(sub)}件】")
for _, r in sub.iterrows():
    pos = r[POSITION_COL] if pd.notna(r[POSITION_COL]) else "(空)"
    print(f"- {r[SPEAKER_COL]} / {r[PARTY_COL]} / 役職={pos} / {str(r[TEXT_COL])[:50]}")

print("\n【藤川政人の段落の役職】")
print(df[df[SPEAKER_COL] == "藤川政人"][POSITION_COL].fillna("(空)").value_counts().to_string())
