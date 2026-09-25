"""
政党別発言数の比較棒グラフ作成

【使用データ】
data/interim/speech_count_by_party.csv
カラム: party, count
"""

import matplotlib.pyplot as plt
import pandas as pd

# --- 日本語フォント設定 ---
plt.rcParams["font.family"] = "Noto Sans CJK JP"

# --- ① データ読み込み ---
df = pd.read_csv("data/interim/speech_count_by_party.csv")

# countの多い順に並べ替え
df = df.sort_values("count", ascending=False)

# --- ② 棒グラフ描画 ---
fig, ax = plt.subplots(figsize=(9, 5))
ax.bar(df["party"], df["count"])

ax.set_title("「消費税」に関する政党別発言数")
ax.set_xlabel("政党")
ax.set_ylabel("発言数")
plt.xticks(rotation=45, ha="right")

plt.tight_layout()

# --- ③ 保存 ---
plt.savefig("output/party_bar.png", dpi=150)

print(df)
