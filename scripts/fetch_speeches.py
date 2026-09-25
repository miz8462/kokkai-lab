"""
国会会議録検索システムAPIから、指定条件の発言を全件取得するスクリプト。

条件: 直近1年・本会議・検索語「消費税」
出力: data/raw/speeches_YYYYMMDD.json (生データをそのまま保存)
"""
import json
import time
from datetime import date, timedelta
from pathlib import Path

import requests

BASE_URL = "https://kokkai.ndl.go.jp/api/speech"
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "raw"
SLEEP_SECONDS = 3  # 利用規約に配慮し、リクエスト間に数秒空ける

today = date.today() # noqa: DTZ011
one_year_ago = today - timedelta(days=365)

BASE_PARAMS = {
    "any": "消費税",
    "nameOfMeeting": "本会議",
    "from": one_year_ago.isoformat(),
    "until": today.isoformat(),
    "maximumRecords": 100,  # speech出力の上限
    "recordPacking": "json",
}


def fetch_all():
    all_records = []
    start_record = 1
    total = None

    while True:
        params = {**BASE_PARAMS, "startRecord": start_record}
        resp = requests.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

        if total is None:
            total = data.get("numberOfRecords", 0)
            print(f"総件数: {total}")

        records = data.get("speechRecord", [])
        all_records.extend(records)
        print(f"  取得済み: {len(all_records)} / {total} (startRecord={start_record})")

        next_pos = data.get("nextRecordPosition")
        if not next_pos:
            break
        start_record = next_pos
        time.sleep(SLEEP_SECONDS)

    return all_records


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    records = fetch_all()

    out_path = OUTPUT_DIR / f"speeches_{today.strftime('%Y%m%d')}.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"\n完了: {len(records)}件を {out_path} に保存しました")


if __name__ == "__main__":
    main()
