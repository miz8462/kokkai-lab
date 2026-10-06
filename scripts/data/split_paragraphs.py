import re

import pandas as pd
from clean_speech import clean_speech

KEYWORD = "消費税"

df = pd.read_csv("data/interim/speeches_extracted.csv")

rows = []
for _, r in df.iterrows():
    # 見出し・自己紹介・末尾の定型句を除去(既存の整形処理を再利用)
    text = clean_speech(str(r["speech"]))

    # 改行で段落に分割し、前後の空白(全角スペース含む)を除去
    paras = [p.strip() for p in re.split(r"\r?\n", text)]
    paras = [p for p in paras if p]  # 空の段落を除外

    for i, p in enumerate(paras, start=1):
        rows.append({
            "speechID": r["speechID"],
            "para_id": i,
            "date": r["date"],
            "speaker": r["speaker"],
            "party": r["party"],
            "speakerPosition": r["speakerPosition"],
            "text": p,
            "has_keyword": KEYWORD in p,
        })

out = pd.DataFrame(rows)
out.to_csv("data/interim/paragraphs.csv", index=False, encoding="utf-8-sig")

print("全段落数:", len(out))
print("「消費税」を含む段落数:", out["has_keyword"].sum())
print(out["text"].str.len().describe())