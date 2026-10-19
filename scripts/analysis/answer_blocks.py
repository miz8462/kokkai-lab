"""
【目的】
政府(role=政府)の段落を、「〜についてお尋ねがありました」などの見出し文で
答弁ブロックに区切り、論点グループごとに「答弁ブロック数」を数える。
段落数は定型答弁の繰り返しで膨らむため、「質問者ごとの答弁1回=1件」に近い
数え方で、政府の応答量を見るためのもの。
見出し文の取りこぼしや誤検出を確認するため、ブロックの一覧も出力する。

【使い方】
python scripts/analysis/answer_blocks.py --slug consumption-tax-issues

【入力】 data/interim/<slug>/paragraphs_clean.csv, data/issues/<slug>.json
【出力】 output/<slug>/answer_blocks.csv (ブロック一覧)
         output/<slug>/answer_blocks_summary.csv (論点別のブロック数)
"""

import argparse
import json
import re
import sys
from pathlib import Path

# scripts/ を sys.path に追加して common を import 可能にする
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd  # noqa: E402
from common import paths  # noqa: E402

HEADING = re.compile(r"お尋ね(が)?(あり|ござい)ました")
HEADING_MAX_LEN = 60


def main() -> None:
    parser = argparse.ArgumentParser(
        description="政府段落を答弁ブロックに区切り、論点グループ別の答弁ブロック数を集計するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    args = parser.parse_args()

    slug: str = args.slug
    p = paths(slug)

    in_path = p["interim"] / "paragraphs_clean.csv"
    groups_path = p["groups"]
    out_blocks = p["output"] / "answer_blocks.csv"
    out_summary = p["output"] / "answer_blocks_summary.csv"

    if not in_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {in_path}")
    if not groups_path.exists():
        raise FileNotFoundError(f"語群定義ファイルが見つかりません: {groups_path}")

    with groups_path.open("r", encoding="utf-8") as f:
        groups = json.load(f)

    df = pd.read_csv(in_path)
    for col in ["exclude", "kw_extended"]:
        df[col] = df[col].astype(str).str.lower().isin(["true", "1"])
    df["text"] = df["text"].fillna("")

    gov = df[df["role"] == "政府"].sort_values(["speechID", "para_id"]).copy()
    gov["is_heading"] = gov["text"].map(
        lambda t: bool(HEADING.search(str(t))) and len(str(t)) < HEADING_MAX_LEN
    )

    # 同じ speechID の中で、見出し文が出るたびにブロック番号を進める
    gov["block"] = gov.groupby("speechID")["is_heading"].cumsum()
    gov["block_id"] = gov["speechID"] + "#" + gov["block"].astype(str)

    # 対象段落(拡張語を含み、除外でない)を含むブロックだけ残す
    target = gov[gov["kw_extended"] & (~gov["exclude"])]
    rows = []
    for name, words in groups.items():
        pattern = "|".join(words)
        hit = target[target["text"].str.contains(pattern, na=False, regex=True)]
        rows.append({
            "論点": name,
            "政府段落": len(hit),
            "答弁ブロック": hit["block_id"].nunique(),
        })

    summary = pd.DataFrame(rows)
    summary["段落/ブロック"] = (summary["政府段落"] / summary["答弁ブロック"]).round(2)
    p["output"].mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_summary, index=False)

    blocks = target.groupby("block_id").agg(
        date=("date", "first"),
        speaker=("speaker", "first"),
        段落数=("para_id", "count"),
        冒頭=("text", lambda s: s.iloc[0][:40]),
    ).reset_index()
    blocks.to_csv(out_blocks, index=False)

    print(f"政府の見出し文: {int(gov['is_heading'].sum())}件")
    print(summary.to_string(index=False))
    print(f"{out_summary} と {out_blocks} に書き出しました")


if __name__ == "__main__":
    main()