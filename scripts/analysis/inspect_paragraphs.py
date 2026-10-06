import pandas as pd

df = pd.read_csv("data/interim/paragraphs.csv")
kw = df[df["has_keyword"]]

print("「消費税」を含む段落が属する発言の数:", kw["speechID"].nunique())

print("\n発言者の役職(上位15):")
print(kw["speakerPosition"].value_counts(dropna=False).head(15))

print("\n政党別の段落数:")
print(kw["party"].value_counts(dropna=False))

# 各発言の第1段落の先頭40文字(削られすぎていないかの確認用)
first = df[df["para_id"] == 1]
print("\n第1段落の先頭40文字(10件):")
print(first["text"].str[:40].head(10).to_string())
