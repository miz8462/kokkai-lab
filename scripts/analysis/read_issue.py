"""
read_issue.py — 論点グループの該当段落を、読みやすいMarkdownにするスクリプト

目的:
  論点グループ(例: A 負担の公平)に入る段落を、日付ごとに
  「議員」と「政府」に分け、政党・発言者・前後の段落つきで出力する。
  論点の内部の対立(どの対策を選ぶか)を、手で読んで整理するための素材にする。

使い方:
  python scripts/analysis/read_issue.py --slug consumption-tax-issues A            # 前後1段落
  python scripts/analysis/read_issue.py --slug consumption-tax-issues C 2          # 前後2段落
  python scripts/analysis/read_issue.py --slug consumption-tax-issues E 1 インボイス  # 語を1つに絞る

入力:
  data/interim/<slug>/paragraphs_clean.csv
  data/issues/<slug>.json
出力:
  output/<slug>/issue_<論点ID>.md
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


def render(r: Any, mark: bool = False) -> str:
    who = f"{r.speaker}({r.party or r.speakerPosition or r.role})"
    head = f"**{who}**" if mark else f"{who}"
    return f"{head}: {r.text}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="論点グループの該当段落をMarkdownとして出力するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    parser.add_argument("gid", help="論点ID (例: A)")
    parser.add_argument("n_ctx", nargs="?", type=int, default=1, help="前後の段落数 (既定値: 1)")
    parser.add_argument("only_term", nargs="?", default=None, help="特定の語に絞る場合の語")
    args = parser.parse_args()

    slug: str = args.slug
    gid: str = args.gid
    n_ctx: int = args.n_ctx
    only_term: str | None = args.only_term

    p = paths(slug)
    in_path = p["interim"] / "paragraphs_clean.csv"
    groups_path = p["groups"]
    out_path = p["output"] / f"issue_{gid}.md"

    if not in_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {in_path}")
    if not groups_path.exists():
        raise FileNotFoundError(f"語群定義ファイルが見つかりません: {groups_path}")

    with groups_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    key = next(k for k in raw if k == gid or k.split()[0] == gid)
    val = raw[key]
    terms = (val.get("terms") or val.get("words") or []) if isinstance(val, dict) else val
    if only_term:
        terms = [only_term]

    df = pd.read_csv(in_path)
    df["exclude"] = df["exclude"].astype(str).str.lower().isin(["true", "1"])
    df["text"] = df["text"].fillna("")
    df["party"] = df["party"].fillna("")
    has_kw = df["kw_extended"].astype(str).str.lower().isin(["true", "1"])
    by_pos = {(r.speechID, r.para_id): r for r in df.itertuples()}

    hits = df[has_kw & (df["role"] != "委員長報告") & (~df["exclude"])].copy()
    hits["matched"] = hits["text"].apply(lambda s: [t for t in terms if t in s])
    hits = hits[hits["matched"].str.len() > 0]

    lines = [f"# 論点 {key}(語: {' / '.join(terms)})", f"該当 {len(hits)} 段落\n"]
    for date, day in hits.sort_values(["date", "speechID", "para_id"]).groupby("date"):
        lines.append(f"## {date}")
        for label, roles in [("議員", ["議員"]), ("政府", ["政府", "議長"])]:
            part = day[day["role"].isin(roles)]
            if part.empty:
                continue
            lines.append(f"### {label}({len(part)}段落)")
            for r in part.itertuples():
                matched = [str(t) for t in r.matched]  # pyright: ignore
                lines.append(f"- 一致語: {', '.join(matched)}")

                for off in range(-n_ctx, n_ctx + 1):
                    p_row = by_pos.get((str(r.speechID), int(r.para_id) + off))  # pyright: ignore
                    if p_row is None:
                        continue
                    lines.append(("  - ▶ " if off == 0 else "  - ") + render(p_row, off == 0))
                lines.append("")

    p["output"].mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"{out_path} に書き出しました({len(hits)}段落)")


if __name__ == "__main__":
    main()
