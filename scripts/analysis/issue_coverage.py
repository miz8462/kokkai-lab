"""
【目的】
data/issues/<slug>.json の語群が、うまく機能しているかを検査する。
(1) 語ごとの該当段落数を出す。一般的すぎる語(多くの無関係な段落を拾う語)を
    見つけるため。
(2) どのグループにも入らなかった段落を、政党・役職つきで output/<slug>/uncovered.md に
    書き出す。語群が見落とした論点を探すための材料になる。
(3) グループに入った段落数と、入らなかった段落数の割合を出す。

【使い方】
python scripts/analysis/issue_coverage.py --slug consumption-tax-issues

【入力】 data/interim/<slug>/paragraphs_clean.csv, data/issues/<slug>.json
【出力】 output/<slug>/uncovered.md(未分類の段落一覧)、画面に語別の件数と網羅率
"""

import argparse
import json
import sys
from pathlib import Path

# scripts/ を sys.path に追加して common を import 可能にする
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd  # noqa: E402
from common import paths  # noqa: E402

TEXT_COL = "text"
PARTY_COL = "party"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="語群の該当段落数や未分類の段落(網羅率)を検査するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    args = parser.parse_args()

    slug: str = args.slug
    p = paths(slug)

    in_path = p["interim"] / "paragraphs_clean.csv"
    groups_path = p["groups"]
    out_path = p["output"] / "uncovered.md"

    if not in_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {in_path}")
    if not groups_path.exists():
        raise FileNotFoundError(f"語群定義ファイルが見つかりません: {groups_path}")

    with groups_path.open("r", encoding="utf-8") as f:
        groups = json.load(f)

    df = pd.read_csv(in_path)
    df["exclude"] = df["exclude"].astype(str).str.lower().isin(["true", "1"])
    df["kw_extended"] = df["kw_extended"].astype(str).str.lower().isin(["true", "1"])
    df = df[df["kw_extended"] & (df["role"] != "委員長報告") & (~df["exclude"])].copy()

    print("【語ごとの該当段落数】")
    all_words = []
    for name, words in groups.items():
        counts = {w: int(df[TEXT_COL].str.contains(w, na=False).sum()) for w in words}
        print(f"{name}: " + " / ".join(f"{w}{n}" for w, n in counts.items()))
        all_words += words

    pattern = "|".join(all_words)
    covered = df[TEXT_COL].str.contains(pattern, na=False, regex=True)
    print(f"\n【網羅率】グループのどれかに入った段落: {int(covered.sum())} / {len(df)}")

    rest = df[~covered]
    lines = [f"# 未分類の段落: {len(rest)}件\n"]
    for _, r in rest.iterrows():
        who = r[PARTY_COL] if r["role"] == "議員" else r["role"]
        lines.append(f"- [{who}] {str(r[TEXT_COL]).replace(chr(10), ' ')}\n")

    p["output"].mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"未分類の段落 {len(rest)}件を {out_path} に書き出しました")


if __name__ == "__main__":
    main()
