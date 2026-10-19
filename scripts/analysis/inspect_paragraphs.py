"""
inspect_paragraphs.py — 段落分割とクリーニングの結果を目で確かめるスクリプト

目的:
  split_paragraphs.py で作った paragraphs.csv が、想定どおりかを点検する。
  「消費税」を含む段落が属する発言の数、発言者の役職(上位15)、政党別の段落数、
  各発言の第1段落の先頭40文字(クリーニングで冒頭を削りすぎていないかの確認)を出す。
  データは書き換えない。新しいテーマで段落分割をやり直したあとの、最初の点検に使う。

使い方:
  python scripts/analysis/inspect_paragraphs.py

入力:
  data/interim/consumption-tax-issues/paragraphs.csv
出力:
  画面表示のみ
"""

import pandas as pd

df = pd.read_csv("data/interim/consumption-tax-issues/paragraphs.csv")
kw = df[df["kw_extended"]]

print("「消費税」を含む段落が属する発言の数:", kw["speechID"].nunique())

print("\n発言者の役職(上位15):")
print(kw["speakerPosition"].value_counts(dropna=False).head(15))

print("\n政党別の段落数:")
print(kw["party"].value_counts(dropna=False))

# 各発言の第1段落の先頭40文字(削られすぎていないかの確認用)
first = df[df["para_id"] == 1]
print("\n第1段落の先頭40文字(10件):")
print(first["text"].str[:40].head(10).to_string())
