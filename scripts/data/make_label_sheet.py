from pathlib import Path

import pandas as pd

THEME = "消費税"
LABEL_VERSION = "v0"  # ラベル定義のバージョン(定義を変えたら上げる)
OUT = Path("data/labels/labels.csv")

if OUT.exists():
    raise SystemExit(f"{OUT} は既にあります。手作業のラベルを守るため、中止します。")

df = pd.read_csv("data/interim/paragraphs.csv")

# 同じ発言の中で、前後の段落を取り出す(文脈を見て判断するため)
df = df.sort_values(["speechID", "para_id"]).reset_index(drop=True)
df["prev_text"] = df.groupby("speechID")["text"].shift(1).fillna("")
df["next_text"] = df.groupby("speechID")["text"].shift(-1).fillna("")


def classify_role(position) -> str:
    """役職の有無から、政府答弁・議員発言・議長を判定する。"""
    if pd.isna(position):
        return "議員"
    if "議長" in str(position):
        return "議長"
    return "政府"


df["role"] = df["speakerPosition"].map(classify_role)

# ラベル付けの対象は「消費税」を含む段落
target = df[df["has_keyword"]].copy()
target["theme"] = THEME
for col in ["topics", "stance", "note"]:
    target[col] = ""  # 手作業で埋める列
target["label_version"] = LABEL_VERSION

cols = [
    "speechID", "para_id", "theme", "party", "role", "speaker",
    "text", "prev_text", "next_text",
    "topics", "stance", "note", "label_version",
]
OUT.parent.mkdir(parents=True, exist_ok=True)
target[cols].to_csv(OUT, index=False, encoding="utf-8-sig")

print("ラベル付け対象:", len(target))
print(target["role"].value_counts())
print(pd.crosstab(target["party"], target["role"]))
