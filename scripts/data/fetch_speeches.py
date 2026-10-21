"""
国会会議録検索システムAPIから、指定条件の発言を全件取得するスクリプト。

条件: config/<slug>.json に定義された keyword, meeting、および直近1年
出力: data/raw/<slug>/speeches_YYYYMMDD.json (生データをそのまま保存)

使い方:
  python scripts/data/fetch_speeches.py --slug consumption-tax-issues
  python scripts/data/fetch_speeches.py --slug consumption-tax-issues --force
"""
import argparse
import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Any

# scripts/ を sys.path に追加して common を import 可能にする
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import requests  # noqa: E402
from common import load_config, paths  # noqa: E402

BASE_URL = "https://kokkai.ndl.go.jp/api/speech"
SLEEP_SECONDS = 3  # 利用規約に配慮し、リクエスト間に数秒空ける


def fetch_all(base_params: dict[str, Any]) -> list[dict[str, Any]]:
    all_records: list[dict[str, Any]] = []
    start_record = 1
    total: int | None = None

    while True:
        params = {**base_params, "startRecord": start_record}
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="国会会議録検索システムAPIから発言データを取得するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    parser.add_argument("--force", action="store_true", help="同名ファイルが存在する場合に上書きする")
    args = parser.parse_args()

    slug: str = args.slug
    force: bool = args.force

    config = load_config(slug)
    p = paths(slug)
    raw_dir = p["raw"]

    if "period_days" not in config:
        raise KeyError(f"config に 'period_days' キーがありません: {config}")

    today = date.today()  # noqa: DTZ011
    one_year_ago = today - timedelta(days=config["period_days"])

    base_params = {
        "any": config["keyword"],
        "nameOfMeeting": config["meeting"],
        "from": one_year_ago.isoformat(),
        "until": today.isoformat(),
        "maximumRecords": 100,  # speech出力の上限
        "recordPacking": "json",
    }

    out_path = raw_dir / f"speeches_{today.strftime('%Y%m%d')}.json"
    if out_path.exists() and not force:
        raise FileExistsError(
            f"出力先ファイルが既に存在します: {out_path}。上書きする場合は --force を指定してください。"
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    records = fetch_all(base_params)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"\n完了: {len(records)}件を {out_path} に保存しました")


if __name__ == "__main__":
    main()
