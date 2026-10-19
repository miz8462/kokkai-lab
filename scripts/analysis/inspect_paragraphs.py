"""
inspect_paragraphs.py — 段落分割とクリーニングの結果を目で確かめるスクリプト

目的:
  split_paragraphs.py で作った paragraphs.csv が、想定どおりかを点検する。
  キーワードを含む段落が属する発言の数、発言者の役職(上位15)、政党別の段落数、
  各発言の第1段落の先頭40文字(クリーニングで冒頭を削りすぎていないかの確認)を出す。
  データは書き換えない。新しいテーマで段落分割をやり直したあとの、最初の点検に使う。

使い方:
  python scripts/analysis/inspect_paragraphs.py --slug consumption-tax-issues

入力:
  data/interim/<slug>/paragraphs.csv
出力:
  画面表示のみ
"""

import argparse
import sys
from pathlib import Path

# scripts/ を sys.path に追加して common を import 可能にする
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd  # noqa: E402
from common import load_config, paths  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="段落分割とクリーニングの結果を点検するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    args = parser.parse_args()

    slug: str = args.slug
    config = load_config(slug)
    keyword: str = config["keyword"]
    p = paths(slug)

    in_path = p["interim"] / "paragraphs.csv"
    if not in_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {in_path}")

    df = pd.read_csv(in_path)
    kw = df[df["kw_extended"]]

    print(f"「{keyword}」を含む段落が属する発言の数:", kw["speechID"].nunique())

    print("\n発言者の役職(上位15):")
    print(kw["speakerPosition"].value_counts(dropna=False).head(15))

    print("\n政党別の段落数:")
    print(kw["party"].value_counts(dropna=False))

    # 各発言の第1段落の先頭40文字(削られすぎていないかの確認用)
    first = df[df["para_id"] == 1]
    print("\n第1段落の先頭40文字(10件):")
    print(first["text"].str[:40].head(10).to_string())


if __name__ == "__main__":
    main()
