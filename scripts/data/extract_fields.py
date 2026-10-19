"""
生データから分析に必要なフィールドを抽出して中間ファイルに保存するスクリプト。

入力: data/raw/<slug>/speeches_YYYYMMDD.json (最新ファイル)
出力: data/interim/<slug>/speeches_extracted.csv

抽出フィールド:
  speechID, date, speaker, speakerGroup, speakerPosition, speech
  + party (speakerGroup を party_mapping で政党名に正規化したもの)

使い方:
  python scripts/data/extract_fields.py --slug consumption-tax-issues
"""
import argparse
import json
import sys
from pathlib import Path
from typing import TypedDict, cast

# scripts/ を sys.path に追加して common を import 可能にする
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd  # noqa: E402
from common import paths  # noqa: E402
from party_mapping import normalize_party  # noqa: E402


class SpeechRecord(TypedDict):
    """生データのレコードのうち、抽出に使うフィールドのみを型付けする。"""

    speechID: str
    date: str
    speaker: str
    speakerGroup: str
    speakerPosition: str | None
    speech: str


def load_latest_raw(raw_dir: Path) -> Path:
    files = sorted(raw_dir.glob("speeches_*.json"))
    if not files:
        raise FileNotFoundError(f"{raw_dir} に speeches_*.json が見つかりません")
    return files[-1]


def load_records(path: Path) -> list[SpeechRecord]:
    with path.open(encoding="utf-8") as f:
        return cast(list[SpeechRecord], json.load(f))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="生データから分析に必要なフィールドを抽出するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    args = parser.parse_args()

    slug: str = args.slug
    p = paths(slug)
    raw_dir = p["raw"]
    interim_dir = p["interim"]

    raw_path = load_latest_raw(raw_dir)
    records = load_records(raw_path)

    rows: list[dict[str, str | None]] = []
    for r in records:
        rows.append({
            "speechID": r["speechID"],
            "date": r["date"],
            "speaker": r["speaker"],
            "speakerGroup": r["speakerGroup"],
            "speakerPosition": r.get("speakerPosition"),
            "speech": r["speech"],
            "party": normalize_party(r["speakerGroup"]),
        })

    df = pd.DataFrame(rows)

    interim_dir.mkdir(parents=True, exist_ok=True)
    out_path = interim_dir / "speeches_extracted.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")

    print(f"入力: {raw_path} ({len(records)}件)")
    print(f"出力: {out_path}")
    print("抽出フィールド: speechID, date, speaker, speakerGroup, speakerPosition, speech, party")
    print()
    print("=== 先頭5件 (date / speaker / party / speakerPosition) ===")
    print(df[["date", "speaker", "party", "speakerPosition"]].head().to_string(index=False))
    print()
    print("=== 政党別件数 ===")
    print(df["party"].value_counts().to_string())


if __name__ == "__main__":
    main()