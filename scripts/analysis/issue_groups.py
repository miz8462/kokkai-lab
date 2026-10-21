"""
【目的】
data/issues/<slug>.json で定義した論点グループごとに、
対象語を含む段落(委員長報告を除く)での広がりを集計する。
グループのいずれかの語を含む段落を、そのグループの段落とみなす。
出すもの: 段落数、議員段落/政府段落、議員の発言者数、議員の最多発言者と割合、
         政党別の発言者数(段落数ではなく人数)。
記事のチャートの元データになる。語の組み分けは自分で決めた定義なので、
記事では語群をそのまま明示する。

【使い方】
python scripts/analysis/issue_groups.py --slug consumption-tax-issues

【入力】 data/interim/<slug>/paragraphs_clean.csv, data/issues/<slug>.json
【出力】 output/<slug>/issue_groups.csv(画面にも表示)
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
from common import load_config, paths  # noqa: E402

TEXT_COL = "text"
SPEAKER_COL = "speaker"
PARTY_COL = "party"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="論点グループごとの発言の広がりを集計するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    args = parser.parse_args()

    slug: str = args.slug
    config = load_config(slug)
    p = paths(slug)

    in_path = p["interim"] / "paragraphs_clean.csv"
    groups_path = p["groups"]
    out_path = p["output"] / "issue_groups.csv"

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

    rows = []
    for name, words in groups.items():
        pattern = "|".join(words)
        sub = df[df[TEXT_COL].str.contains(pattern, na=False, regex=True)]
        mem = sub[sub["role"] == "議員"]
        top = mem[SPEAKER_COL].value_counts()
        # 同点の場合は発言者名で昇順に固定
        top = top.sort_values(ascending=False)
        top = top.reset_index()
        top.columns = ["speaker", "count"]
        top = top.sort_values(["count", "speaker"], ascending=[False, True])
        top_dict = dict(zip(top["speaker"], top["count"]))
        by_party_series = mem.groupby(PARTY_COL)[SPEAKER_COL].nunique()
        by_party = by_party_series.sort_values(ascending=False)
        # 同点の場合は政党名で昇順に固定
        by_party = by_party.reset_index()
        by_party.columns = ["party", "count"]
        by_party = by_party.sort_values(["count", "party"], ascending=[False, True])
        by_party = dict(zip(by_party["party"], by_party["count"]))
        rows.append({
            "論点": name,
            "段落": len(sub),
            "議員段落": len(mem),
            "政府段落": int((sub["role"] == "政府").sum()),
            "議員の発言者": mem[SPEAKER_COL].nunique(),
            "議員の最多": next(iter(top_dict.keys())) if top_dict else "",
            "最多の割合": round(next(iter(top_dict.values())) / len(mem), 2) if top_dict else 0,
            "政党別の発言者数": " ".join(f"{p}{n}" for p, n in by_party.items()),
        })

    res = pd.DataFrame(rows)
    p["output"].mkdir(parents=True, exist_ok=True)
    res.to_csv(out_path, index=False)

    keyword: str = config["keyword"]
    extra_terms: list[str] = config.get("extra_terms", [])
    seen_base = set()
    display_terms: list[str] = []
    for t in [keyword] + extra_terms:
        norm = t.replace("付き", "つき")
        if norm not in seen_base:
            seen_base.add(norm)
            display_terms.append(t)
    terms_label = "・".join(display_terms)

    print(f"対象: {terms_label}を含む段落(委員長報告・除外分を除く) {len(df)}件")
    print(res.to_string(index=False))


if __name__ == "__main__":
    main()
