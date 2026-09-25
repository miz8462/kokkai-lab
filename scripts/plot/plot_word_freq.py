"""
頻出語ランキングの可視化(全体版)

【使用データ】
data/interim/word_freq.csv
カラム: word, count (想定。違う場合は下の読み込み部分を調整)
"""

import matplotlib.pyplot as plt
import pandas as pd

# --- 日本語フォント設定 ---
plt.rcParams["font.family"] = "Noto Sans CJK JP"

# --- ① データ読み込み ---
df = pd.read_csv("data/interim/word_freq.csv")

# 上位20語に絞る(全部だと見づらいため)
TOP_N = 20
df_top = df.sort_values("count", ascending=False).head(TOP_N)

# --- ② 棒グラフ描画(横棒: 単語が多いと縦棒はラベルが潰れるため) ---
fig, ax = plt.subplots(figsize=(8, 8))
# 上位語を上に表示したいので反転
ax.barh(df_top["word"][::-1], df_top["count"][::-1])

ax.set_title(f"「消費税」関連発言の頻出語ランキング(上位{TOP_N}語)")
ax.set_xlabel("出現回数")
ax.set_ylabel("単語")

plt.tight_layout()

# --- ③ 保存 ---
plt.savefig("output/word_freq_top20.png", dpi=150)

print(df_top)
