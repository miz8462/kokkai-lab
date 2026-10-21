"""
issue_sub.py — 論点のサブグループ別に、議員・政府の段落数と政党別の発言者数を出すスクリプト

目的:
  issue_A_sub.json のような「サブ論点の語群」を読み、サブ論点ごとに
  段落数・議員/政府の内訳・議員の発言者数・政党別の発言者数を出す。
  特に A2(食料品だけか一律か)で、どの政党がどの立場の語を使うかを見る。

使い方:
  python scripts/analysis/issue_sub.py --slug consumption-tax-issues data/issues/issue_A_sub.json

入力:
  data/interim/<slug>/paragraphs_clean.csv, 引数で指定したJSON
出力:
  標準出力と output/<slug>/issue_sub.csv
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
from common import BASE, paths  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="サブ論点グループ別に段落数と政党別発言者数を集計するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    parser.add_argument(
        "sub_json",
        nargs="?",
        default="data/issues/issue_A_sub.json",
        help="サブ論点の定義JSONファイルパス (既定値: data/issues/issue_A_sub.json)",
    )
    args = parser.parse_args()

    slug: str = args.slug
    sub_json_arg: str = args.sub_json
    p = paths(slug)

    sub_json_path = Path(sub_json_arg)
    if not sub_json_path.is_absolute():
        sub_json_path = BASE / sub_json_path

    if not sub_json_path.exists():
        raise FileNotFoundError(f"サブ論点ファイルが見つかりません: {sub_json_path}")

    with sub_json_path.open("r", encoding="utf-8") as f:
        groups = json.load(f)

    in_path = p["interim"] / "paragraphs_clean.csv"
    out_path = p["output"] / "issue_sub.csv"

    if not in_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {in_path}")

    df = pd.read_csv(in_path)
    df["exclude"] = df["exclude"].astype(str).str.lower().isin(["true", "1"])
    df["text"] = df["text"].fillna("")
    df["party"] = df["party"].fillna("")
    has_kw = df["kw_extended"].astype(str).str.lower().isin(["true", "1"])
    df = df[has_kw & (df["role"] != "委員長報告") & (~df["exclude"])].copy()
    print(f"対象: {len(df)}件")

    rows = []
    for name, terms in groups.items():
        hit = df["text"].apply(lambda s: any(t in s for t in terms))
        sub = df[hit]
        mem = sub[sub["role"] == "議員"]
        top = mem["speaker"].value_counts()
        # 同点の場合は発言者名で昇順に固定
        top = top.sort_values(ascending=False)
        top = top.reset_index()
        top.columns = ["speaker", "count"]
        top = top.sort_values(["count", "speaker"], ascending=[False, True])
        top_dict = dict(zip(top["speaker"], top["count"]))
        party_n_series = mem.groupby("party")["speaker"].nunique()
        party_n = party_n_series.sort_values(ascending=False)
        # 同点の場合は政党名で昇順に固定
        party_n = party_n.reset_index()
        party_n.columns = ["party", "count"]
        party_n = party_n.sort_values(["count", "party"], ascending=[False, True])
        party_n = dict(zip(party_n["party"], party_n["count"]))
        rows.append({
            "サブ論点": name,
            "段落": len(sub),
            "議員段落": len(mem),
            "政府段落": int((sub["role"] == "政府").sum()),
            "議員の発言者": mem["speaker"].nunique(),
            "議員の最多": next(iter(top_dict.keys())) if top_dict else "",
            "最多の割合": round(next(iter(top_dict.values())) / len(mem), 2) if top_dict else 0,
            "政党別の発言者数": " ".join(f"{p}{n}" for p, n in party_n.items()),
        })

    res = pd.DataFrame(rows)
    p["output"].mkdir(parents=True, exist_ok=True)
    res.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(res.to_string(index=False))
    print(f"\n{out_path} に書き出しました")


if __name__ == "__main__":
    main()
