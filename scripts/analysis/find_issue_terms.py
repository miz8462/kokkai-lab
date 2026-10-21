"""
find_issue_terms.py — 対象キーワードを含む段落に特徴的な名詞を探し、論点の語の候補を出すスクリプト

目的:
  論点の語を自分で決め打ちせず、議論の中から出てきた語だけで抽出するための材料を作る。
  キーワードを含む段落(対象)と含まない段落(基準)で、名詞の出現段落率を比べ、
  対象に偏って出る名詞を、対数オッズ比(+0.5で平滑化)の高い順に並べる。
  複合語を保つため、Sudachi の SplitMode.C で分割する。
  語の偏りが1人の発言に由来していないかは、term_spread.py で別途確かめる。

使い方:
  python scripts/analysis/find_issue_terms.py --slug consumption-tax-issues

入力:
  data/interim/<slug>/paragraphs.csv
出力:
  output/<slug>/issue_terms.csv(term, df_target, df_rest, score, example)
  画面には上位60語を表示
"""

import argparse
import math
import sys
from pathlib import Path

# scripts/ を sys.path に追加して common を import 可能にする
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd  # noqa: E402
from common import load_config, paths  # noqa: E402
from sudachipy import dictionary, tokenizer  # noqa: E402

TEXT_COL = "text"          # 段落本文の列名
MIN_DF = 4                 # 対象段落での最低出現段落数
MODE = tokenizer.Tokenizer.SplitMode.C  # 複合語(例: 逆進性)を保つ
SKIP_SUB = {"数詞", "代名詞", "非自立可能", "助数詞可能"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="キーワードを含む段落に特徴的な名詞を抽出するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    args = parser.parse_args()

    slug: str = args.slug
    config = load_config(slug)
    keyword: str = config["keyword"]
    p = paths(slug)

    in_path = p["interim"] / "paragraphs.csv"
    out_path = p["output"] / "issue_terms.csv"

    if not in_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {in_path}")

    df = pd.read_csv(in_path)
    if TEXT_COL not in df.columns:
        raise SystemExit(f"列が見つかりません。実際の列名: {list(df.columns)}")

    tok = dictionary.Dictionary().create()

    def nouns(text: str) -> set[str]:
        out = set()
        for m in tok.tokenize(text, MODE):
            pos = m.part_of_speech()
            if pos[0] != "名詞" or pos[1] in SKIP_SUB:
                continue
            w = m.dictionary_form()
            if len(w) >= 2 and w != keyword:
                out.add(w)
        return out

    df["is_target"] = df[TEXT_COL].str.contains(keyword, na=False)
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

    res = pd.DataFrame(rows).sort_values(["score", "term"], ascending=[False, True])
    p["output"].mkdir(parents=True, exist_ok=True)
    res.to_csv(out_path, index=False)
    print(f"対象段落 {nt} / 基準段落 {nr}")
    print(res.head(60).to_string(index=False))


if __name__ == "__main__":
    main()