"""
show_context.py — 指定した語を含む段落を、前後の段落つきで読めるMarkdownにするスクリプト

目的:
  語(例: 滞納、インボイス)が、実際の議論でどんな文脈で使われているかを読むための素材を作る。
  同じ発言(speechID)の中で、該当段落の前後 N 段落を並べる。
  見出しには、政党・役職(role)・対象区分(キーワードあり / 拡張語のみ / 対象外)・除外印を出す。
  行は絞らない(除外印の段落も出す)ので、再掲や議長の議事進行も目で確かめられる。
  論点グループ単位で読むときは read_issue.py を使う。

使い方:
  python scripts/analysis/show_context.py --slug consumption-tax-issues 滞納         # 前後1段落
  python scripts/analysis/show_context.py --slug consumption-tax-issues 滞納 2       # 前後2段落

入力:
  data/interim/<slug>/paragraphs_clean.csv
出力:
  output/<slug>/context.md
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

TEXT_COL = "text"
SPEECH_COL = "speechID"
PARA_COL = "para_id"
PARTY_COL = "party"
POSITION_COL = "speakerPosition"  # roleがないときの代替


def main() -> None:
    parser = argparse.ArgumentParser(
        description="指定した語を含む段落を前後の段落つきで出力するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    parser.add_argument("term", help="検索対象の語")
    parser.add_argument("window", nargs="?", type=int, default=1, help="前後の段落数 (既定値: 1)")
    args = parser.parse_args()

    slug: str = args.slug
    term: str = args.term
    window: int = args.window

    config = load_config(slug)
    keyword: str = config["keyword"]
    p = paths(slug)

    in_path = p["interim"] / "paragraphs_clean.csv"
    out_path = p["output"] / "context.md"

    if not in_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {in_path}")

    df = pd.read_csv(in_path)
    if "exclude" in df.columns:
        df["exclude"] = df["exclude"].astype(str).str.lower().isin(["true", "1"])
    else:
        df["exclude"] = False
    print(f"列名: {list(df.columns)}")

    missing = [c for c in (TEXT_COL, SPEECH_COL, PARA_COL) if c not in df.columns]
    if missing:
        raise SystemExit(f"必須の列がありません: {missing}。上の列名に合わせて先頭の設定を直してください")

    if "role" not in df.columns:
        if POSITION_COL in df.columns:
            has_pos = df[POSITION_COL].notna() & (df[POSITION_COL].astype(str).str.strip() != "")
            df["role"] = has_pos.map({True: "政府", False: "議員"})
        else:
            df["role"] = "不明"
    if PARTY_COL not in df.columns:
        df[PARTY_COL] = "不明"

    df = df.sort_values([SPEECH_COL, PARA_COL]).reset_index(drop=True)

    hits = df.index[df[TEXT_COL].str.contains(term, na=False)]
    lines = [f"# 「{term}」を含む段落: {len(hits)}件\n"]

    for i in hits:
        r = df.loc[i]
        kw = (
            f"{keyword}あり"
            if str(r["has_keyword"]) == "True"
            else ("拡張語のみ" if str(r["kw_extended"]) == "True" else "対象語なし")
        )
        ex = " / 除外" if r["exclude"] else ""
        lines.append(f"## {r[PARTY_COL]} / {r['role']} / {kw}{ex} / {r[SPEECH_COL]}-{r[PARA_COL]}\n")
        for j in range(i - window, i + window + 1):
            if j < 0 or j >= len(df) or df.loc[j, SPEECH_COL] != r[SPEECH_COL]:
                continue
            mark = "**▶** " if j == i else "　 "
            lines.append(f"{mark}{df.loc[j, TEXT_COL]}\n")
        lines.append("")

    p["output"].mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"{len(hits)}件を {out_path} に書き出しました")


if __name__ == "__main__":
    main()
