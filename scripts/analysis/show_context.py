# scripts/analysis/show_context.py
import sys
import pandas as pd

# --- ここだけ自分のCSVに合わせて直す ---
INPUT = "data/interim/paragraphs.csv"
TEXT_COL = "text"
SPEECH_COL = "speechID"
PARA_COL = "para_id"
PARTY_COL = "party"
POSITION_COL = "speakerPosition"  # roleがないときの代替
OUTPUT = "output/context.md"
# ---------------------------------------

term = sys.argv[1]
window = int(sys.argv[2]) if len(sys.argv) > 2 else 1

df = pd.read_csv(INPUT)
print(f"列名: {list(df.columns)}")

missing = [c for c in (TEXT_COL, SPEECH_COL, PARA_COL) if c not in df.columns]
if missing:
    raise SystemExit(f"必須の列がありません: {missing}。上の列名に合わせて先頭の設定を直してください")

if "role" not in df.columns:
    if POSITION_COL in df.columns:
        has_pos = df[POSITION_COL].notna() & (df[POSITION_COL].astype(str).str.strip() != "")
        df["role"] = has_pos.map({True: "政府", False: "議員"})
    else:
        df["role"] = "不明"
if PARTY_COL not in df.columns:
    df[PARTY_COL] = "不明"

df = df.sort_values([SPEECH_COL, PARA_COL]).reset_index(drop=True)

hits = df.index[df[TEXT_COL].str.contains(term, na=False)]
lines = [f"# 「{term}」を含む段落: {len(hits)}件\n"]

for i in hits:
    r = df.loc[i]
    kw = "消費税あり" if str(r["has_keyword"]) == "True" else "消費税なし"
    lines.append(f"## {r[PARTY_COL]} / {r['role']} / {kw} / {r[SPEECH_COL]}-{r[PARA_COL]}\n")
    for j in range(i - window, i + window + 1):
        if j < 0 or j >= len(df) or df.loc[j, SPEECH_COL] != r[SPEECH_COL]:
            continue
        mark = "**▶** " if j == i else "　 "
        lines.append(f"{mark}{df.loc[j, TEXT_COL]}\n")
    lines.append("")

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"{len(hits)}件を {OUTPUT} に書き出しました")