"""
生データから分析に必要なフィールドを抽出して中間ファイルに保存するスクリプト。

入力: data/raw/speeches_YYYYMMDD.json (最新ファイル)
出力: data/interim/speeches_extracted.csv

抽出フィールド:
  speechID, date, speaker, speakerGroup, speakerPosition, speech
  + party (speakerGroup を party_mapping で政党名に正規化したもの)
"""
import json
from pathlib import Path
from typing import TypedDict, cast

import pandas as pd
from party_mapping import normalize_party

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
INTERIM_DIR = BASE_DIR / "data" / "interim"


class SpeechRecord(TypedDict):
    """生データのレコードのうち、抽出に使うフィールドのみを型付けする。"""

    speechID: str
    date: str
    speaker: str
    speakerGroup: str
    speakerPosition: str | None
    speech: str


def load_latest_raw() -> Path:
    files = sorted(RAW_DIR.glob("speeches_*.json"))
    if not files:
        raise FileNotFoundError(f"{RAW_DIR} に speeches_*.json が見つかりません")
    return files[-1]


def load_records(path: Path) -> list[SpeechRecord]:
    with path.open(encoding="utf-8") as f:
        return cast(list[SpeechRecord], json.load(f))


def main():
    raw_path = load_latest_raw()
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

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out_path = INTERIM_DIR / "speeches_extracted.csv"
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