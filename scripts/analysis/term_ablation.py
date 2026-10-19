"""
目的:
  論点グループの各語について、
  - その語を含む段落数
  - 同じグループの中で、その語だけが支えている段落数
  - 全グループの中で、その語だけが支えている段落数(外すと網羅率が下がる数)
  - 他グループの語とも重なる段落数
  を出し、「外してよい語」「他と重なりすぎる語」を数字で判断できるようにする。

使い方:
  python scripts/analysis/term_ablation.py --slug consumption-tax-issues

入力:
  data/interim/<slug>/paragraphs_clean.csv
  data/issues/<slug>.json
出力:
  標準出力(グループ別の表)と output/<slug>/term_ablation.csv
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any

# scripts/ を sys.path に追加して common を import 可能にする
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd  # noqa: E402
from common import paths  # noqa: E402


def load_groups(path: Path) -> dict[str, list[str]]:
    """JSONの形式(語のリスト / name+termsの辞書)のどちらでも読む"""
    with path.open("r", encoding="utf-8") as f:
        raw: dict[str, Any] = json.load(f)
    groups: dict[str, list[str]] = {}
    for key, val in raw.items():
        if isinstance(val, dict):
            terms = val.get("terms") or val.get("words") or []
        else:
            terms = val
        groups[key] = terms
    return groups


def main() -> None:
    parser = argparse.ArgumentParser(
        description="論点グループの各語の寄与度・重複度を分析するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    args = parser.parse_args()

    slug: str = args.slug
    p = paths(slug)

    in_path = p["interim"] / "paragraphs_clean.csv"
    groups_path = p["groups"]
    out_path = p["output"] / "term_ablation.csv"

    if not in_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {in_path}")
    if not groups_path.exists():
        raise FileNotFoundError(f"語群定義ファイルが見つかりません: {groups_path}")

    df = pd.read_csv(in_path)
    df["exclude"] = df["exclude"].astype(str).str.lower().isin(["true", "1"])
    has_kw = df["kw_extended"].astype(str).str.lower().isin(["true", "1"])
    target = df[has_kw & (df["role"] != "委員長報告") & (~df["exclude"])]
    texts = target["text"].fillna("")
    print(f"対象: {len(target)}件")

    groups = load_groups(groups_path)

    hit = {}
    for gid, terms in groups.items():
        for t in terms:
            hit[(gid, t)] = texts.str.contains(t, regex=False)

    total_terms = sum(hit.values())  # 段落ごとの、全グループでの一致語数
    group_count = {
        gid: sum(hit[(gid, t)] for t in terms) for gid, terms in groups.items()
    }

    rows = []
    for (gid, t), s in hit.items():
        rows.append({
            "論点": gid,
            "語": t,
            "該当": int(s.sum()),
            "グループ内でこの語だけ": int((s & (group_count[gid] == 1)).sum()),
            "全体でこの語だけ": int((s & (total_terms == 1)).sum()),
            "他グループにも入る": int((s & ((total_terms - group_count[gid]) > 0)).sum()),
        })

    res = pd.DataFrame(rows)
    p["output"].mkdir(parents=True, exist_ok=True)
    res.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(res.to_string(index=False))
    print(f"\n{out_path} に書き出しました")


if __name__ == "__main__":
    main()
