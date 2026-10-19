"""
split_paragraphs.py — 発言を段落に分け、対象語を含むかの印をつけるスクリプト

目的:
  speeches_extracted.csv の各発言を、clean_speech でノイズ除去したうえで改行ごとに段落へ分け、
  段落単位のCSV(paragraphs.csv)を作る。論点分析は、すべてこの段落が単位になる。
  各段落に、次の2つの印をつける。
    has_keyword: keyword (例: 「消費税」) を含む
    kw_extended: 拡張語 (keyword + extra_terms) のいずれかを含む
  拡張語は、「消費減税」「給付つき税額控除」など keyword を含まずに論点を語る段落を拾うため。
  対象語は config/<slug>.json から読み込む。
  後続: mark_roles.py → dedupe_paragraphs.py の順に実行する。

使い方:
  python scripts/data/split_paragraphs.py --slug consumption-tax-issues

入力:
  data/interim/<slug>/speeches_extracted.csv
出力:
  data/interim/<slug>/paragraphs.csv
  (speechID, para_id, date, speaker, party, speakerPosition, text, has_keyword, kw_extended)
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Any

# scripts/ を sys.path に追加して common を import 可能にする
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd  # noqa: E402
from clean_speech import clean_speech  # noqa: E402
from common import load_config, paths  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="発言を段落に分け、対象語を含むかの印をつけるスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    args = parser.parse_args()

    slug: str = args.slug
    config = load_config(slug)
    p = paths(slug)
    interim_dir = p["interim"]

    keyword: str = config["keyword"]
    extra_terms: list[str] = config.get("extra_terms", [])
    extended_keywords: list[str] = [keyword] + extra_terms

    in_path = interim_dir / "speeches_extracted.csv"
    if not in_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {in_path}")

    df = pd.read_csv(in_path)

    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        # 見出し・自己紹介・末尾の定型句を除去(既存の整形処理を再利用)
        text = clean_speech(str(r["speech"]))

        # 改行で段落に分割し、前後の空白(全角スペース含む)を除去
        paras = [p.strip() for p in re.split(r"\r?\n", text)]
        paras = [p for p in paras if p]  # 空の段落を除外

        for i, para in enumerate(paras, start=1):
            rows.append({
                "speechID": r["speechID"],
                "para_id": i,
                "date": r["date"],
                "speaker": r["speaker"],
                "party": r["party"],
                "speakerPosition": r["speakerPosition"],
                "text": para,
                "has_keyword": keyword in para,
                "kw_extended": any(k in para for k in extended_keywords),
            })

    out = pd.DataFrame(rows)
    interim_dir.mkdir(parents=True, exist_ok=True)
    out_path = interim_dir / "paragraphs.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")

    print("全段落数:", len(out))
    print(f"「{keyword}」を含む段落数:", out["has_keyword"].sum())
    print("拡張語を含む段落数:", out["kw_extended"].sum())
    print(out["text"].str.len().describe())


if __name__ == "__main__":
    main()