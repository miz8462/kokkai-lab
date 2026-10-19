"""
【目的】
論点の候補になった語が、特定の1人の発言に偏っていないかを調べる。
指定した語ごとに、config の keyword(拡張語を含む)に当たる段落での出現段落数・発言数・発言者数・
議員/政府の内訳・議員の最多発言者とその割合・議員の政党別の内訳を出す。
委員長報告(role=委員長報告)は集計から除く。
段落数が多くても1人の長い発言から出ているだけの語は、論点の大きさを
過大に見せるので、それを見分けるために使う。

【使い方】
python scripts/analysis/term_spread.py --slug consumption-tax-issues 滞納 倒産 担税力

【入力】 data/interim/<slug>/paragraphs_clean.csv(scripts/data/mark_roles.py の出力)
【出力】 output/<slug>/term_spread.csv(画面にも同じ表を表示)
"""
import argparse
import sys
from pathlib import Path

# scripts/ を sys.path に追加して common を import 可能にする
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd  # noqa: E402
from common import paths  # noqa: E402

TEXT_COL = "text"
SPEECH_COL = "speechID"
SPEAKER_COL = "speaker"
PARTY_COL = "party"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="論点候補の語が特定の発言者に偏っていないかを調べるスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    parser.add_argument("terms", nargs="+", help="調べる語のリスト (例: 滞納 倒産)")
    args = parser.parse_args()

    slug: str = args.slug
    terms: list[str] = args.terms
    p = paths(slug)

    in_path = p["interim"] / "paragraphs_clean.csv"
    out_path = p["output"] / "term_spread.csv"

    if not in_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {in_path}")

    df = pd.read_csv(in_path)
    df["exclude"] = df["exclude"].astype(str).str.lower().isin(["true", "1"])
    df["kw_extended"] = df["kw_extended"].astype(str).str.lower().isin(["true", "1"])
    df = df[df["kw_extended"] & (df["role"] != "委員長報告") & (~df["exclude"])].copy()

    rows = []
    for t in terms:
        sub = df[df[TEXT_COL].str.contains(t, na=False)]
        if len(sub) == 0:
            rows.append({"term": t, "段落": 0})
            continue
        mem = sub[sub["role"] == "議員"]
        top = mem[SPEAKER_COL].value_counts()
        parties = mem[PARTY_COL].value_counts()
        rows.append({
            "term": t,
            "段落": len(sub),
            "発言": sub[SPEECH_COL].nunique(),
            "議員段落": len(mem),
            "議員の発言者": mem[SPEAKER_COL].nunique(),
            "政府段落": int((sub["role"] == "政府").sum()),
            "議員の最多": top.index[0] if len(top) else "",
            "最多の割合": round(top.iloc[0] / len(mem), 2) if len(top) else 0,
            "議員の政党": " ".join(f"{p}{n}" for p, n in parties.items()),
        })

    res = pd.DataFrame(rows)
    p["output"].mkdir(parents=True, exist_ok=True)
    res.to_csv(out_path, index=False)
    print(res.to_string(index=False))


if __name__ == "__main__":
    main()