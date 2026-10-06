# scripts/analysis/find_issue_terms.py
import math
import pandas as pd
from sudachipy import dictionary, tokenizer

# --- ここだけ自分のCSVに合わせて直す ---
INPUT = "data/interim/paragraphs.csv"
TEXT_COL = "text"          # 段落本文の列名
KEYWORD = "消費税"
MIN_DF = 4                 # 対象段落での最低出現段落数
OUTPUT = "output/issue_terms.csv"
# ---------------------------------------

df = pd.read_csv(INPUT)
if TEXT_COL not in df.columns:
    raise SystemExit(f"列が見つかりません。実際の列名: {list(df.columns)}")

tok = dictionary.Dictionary().create()
MODE = tokenizer.Tokenizer.SplitMode.C  # 複合語(例: 逆進性)を保つ
SKIP_SUB = {"数詞", "代名詞", "非自立可能", "助数詞可能"}


def nouns(text: str) -> set[str]:
    out = set()
    for m in tok.tokenize(text, MODE):
        pos = m.part_of_speech()
        if pos[0] != "名詞" or pos[1] in SKIP_SUB:
            continue
        w = m.dictionary_form()
        if len(w) >= 2 and w != KEYWORD:
            out.add(w)
    return out


df["is_target"] = df[TEXT_COL].str.contains(KEYWORD, na=False)
df["nouns"] = df[TEXT_COL].fillna("").map(nouns)

target = df[df["is_target"]]
rest = df[~df["is_target"]]
nt, nr = len(target), len(rest)


def doc_freq(sub):
    freq = {}
    for s in sub["nouns"]:
        for w in s:
            freq[w] = freq.get(w, 0) + 1
    return freq


ft, fr = doc_freq(target), doc_freq(rest)

rows = []
for w, a in ft.items():
    if a < MIN_DF:
        continue
    b = fr.get(w, 0)
    # 段落単位の出現率の対数オッズ比(+0.5で平滑化)
    score = math.log((a + 0.5) / (nt - a + 0.5)) - math.log((b + 0.5) / (nr - b + 0.5))
    ex = target[target["nouns"].map(lambda s: w in s)].iloc[0][TEXT_COL]
    i = ex.find(w)
    rows.append({
        "term": w,
        "df_target": a,
        "df_rest": b,
        "score": round(score, 2),
        "example": ex[max(0, i - 25): i + 25].replace("\n", " "),
    })

res = pd.DataFrame(rows).sort_values("score", ascending=False)
res.to_csv(OUTPUT, index=False)
print(f"対象段落 {nt} / 基準段落 {nr}")
print(res.head(60).to_string(index=False))