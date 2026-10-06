import pandas as pd

df = pd.read_csv("data/interim/speeches_extracted.csv")

# 1件目の本文の先頭500文字を、改行などを見える形で表示
text = str(df.loc[0, "speech"])
print(repr(text[:500]))

# 改行(\n)の数を、全件で集計
df["n_newlines"] = df["speech"].str.count("\n")
print(df["n_newlines"].describe())
