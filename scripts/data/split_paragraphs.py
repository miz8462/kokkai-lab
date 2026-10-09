"""
split_paragraphs.py — 発言を段落に分け、対象語を含むかの印をつけるスクリプト

目的:
  speeches_extracted.csv の各発言を、clean_speech でノイズ除去したうえで改行ごとに段落へ分け、
  段落単位のCSV(paragraphs.csv)を作る。論点分析は、すべてこの段落が単位になる。
  各段落に、次の2つの印をつける。
    has_keyword: 「消費税」を含む
    kw_extended: 拡張語(消費税・消費減税・給付つき税額控除・給付付き税額控除)のいずれかを含む
  拡張語は、「消費減税」「給付つき税額控除」など「消費税」を含まずに論点を語る段落を拾うため。
  対象語を変えるときは、冒頭の KEYWORD と EXTENDED_KEYWORDS を直す。
  後続: mark_roles.py → dedupe_paragraphs.py の順に実行する。

使い方:
  python scripts/data/split_paragraphs.py

入力:
  data/interim/speeches_extracted.csv
出力:
  data/interim/paragraphs.csv
  (speechID, para_id, date, speaker, party, speakerPosition, text, has_keyword, kw_extended)
"""

import re

import pandas as pd
from clean_speech import clean_speech

KEYWORD = "消費税"
# 「消費税」の語を使わずに論点を語る段落を拾うための拡張語
EXTENDED_KEYWORDS = [KEYWORD, "消費減税", "給付つき税額控除", "給付付き税額控除"]

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
            "kw_extended": any(k in p for k in EXTENDED_KEYWORDS),
        })

out = pd.DataFrame(rows)
out.to_csv("data/interim/paragraphs.csv", index=False, encoding="utf-8-sig")

print("全段落数:", len(out))
print("「消費税」を含む段落数:", out["has_keyword"].sum())
print("拡張語を含む段落数:", out["kw_extended"].sum())
print(out["text"].str.len().describe())