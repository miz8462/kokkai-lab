"""
年別発言数推移の折れ線グラフ作成

【使用データ】
interim/speeches_extracted.csv
カラム: speechID, date, speaker, speakerGroup, speakerPosition, speech, party
1発言 = 1行のデータなので、date列から年を取り出してカウントする。
"""

import matplotlib.pyplot as plt
import pandas as pd

# --- 日本語フォント設定 ---
# 環境に合わせて変更してください
# macOS: "Hiragino Sans"
# Windows: "Yu Gothic" or "MS Gothic"
# Linux: "IPAexGothic" (別途インストールが必要な場合あり)
plt.rcParams["font.family"] = "Noto Sans CJK JP"

# --- ① データ読み込み ---
df = pd.read_csv("data/interim/speeches_extracted.csv")

# date列をdatetime化して年を抽出
df["date"] = pd.to_datetime(df["date"])
df["year"] = df["date"].dt.year

# 年別発言数を集計
yearly_counts = df.groupby("year").size().reset_index(name="count")

# --- ② 折れ線グラフ描画 ---
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(yearly_counts["year"], yearly_counts["count"], marker="o")

ax.set_title("「消費税」に関する年別発言数の推移")
ax.set_xlabel("年")
ax.set_ylabel("発言数")
ax.grid(True, alpha=0.3)
ax.set_xticks(yearly_counts["year"])

plt.tight_layout()

# --- ③ 保存 & 表示 ---
plt.savefig("output/yearly_trend.png", dpi=150)
plt.show()

print(yearly_counts)
