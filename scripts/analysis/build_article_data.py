"""
【目的】
論点別の「議員の発言者数」と「政府の応答回数(答弁ブロック数)」を1つにまとめ、
記事のチャート(Nivo)に渡すJSONを作る。
議員と政府は単位が違う(人数と回数)ので、混ぜずに別のキーで持つ。
政党別の発言者数も同梱する(議員のみ)。

【使い方】
python scripts/analysis/build_article_data.py --slug consumption-tax-issues
(先に issue_groups.py --slug <slug> と answer_blocks.py --slug <slug> を実行しておくこと)

【入力】 output/<slug>/issue_groups.csv, output/<slug>/answer_blocks_summary.csv
【出力】 data/article/<slug>.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# scripts/ を sys.path に追加して common を import 可能にする
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import pandas as pd  # noqa: E402
from common import load_config, paths  # noqa: E402


def build_source_text(config: dict[str, Any], count: int) -> str:
    period = config.get("period", "直近1年")
    meeting = config.get("meeting", "本会議")
    keyword = config.get("keyword", "")
    extra_terms: list[str] = config.get("extra_terms", [])

    terms = [keyword] + extra_terms
    seen = set()
    formatted = []
    for t in terms:
        if not t or t in seen:
            continue
        if "つき" in t:
            alt = t.replace("つき", "付き")
            if alt in terms:
                merged = t.replace("つき", "つき(付き)")
                formatted.append(f"「{merged}」")
                seen.add(t)
                seen.add(alt)
                continue
        elif "付き" in t:
            alt = t.replace("付き", "つき")
            if alt in terms:
                continue
        formatted.append(f"「{t}」")
        seen.add(t)

    terms_str = "".join(formatted)
    return (
        f"国会会議録検索システム(国立国会図書館) {period}の{meeting}における発言。"
        f"{terms_str}のいずれかを含む段落{count}件"
        f"(委員長報告・議長の議事進行・同一演説の再掲を除く)を集計"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="論点別の議員発言者数と政府応答回数を集約し記事用JSONを生成するスクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    args = parser.parse_args()

    slug: str = args.slug
    config = load_config(slug)
    p = paths(slug)

    issues_path = p["output"] / "issue_groups.csv"
    blocks_path = p["output"] / "answer_blocks_summary.csv"
    out_path = p["article"]
    paragraphs_path = p["interim"] / "paragraphs_clean.csv"
    groups_path = p["groups"]

    if not issues_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {issues_path}")
    if not blocks_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {blocks_path}")
    if not paragraphs_path.exists():
        raise FileNotFoundError(f"入力ファイルが見つかりません: {paragraphs_path}")
    if not groups_path.exists():
        raise FileNotFoundError(f"語群定義ファイルが見つかりません: {groups_path}")

    issues = pd.read_csv(issues_path)
    blocks = pd.read_csv(blocks_path).set_index("論点")

    # 政党別の発言者名リストを paragraphs_clean.csv から集計
    df_p = pd.read_csv(paragraphs_path)
    df_p["exclude"] = df_p["exclude"].astype(str).str.lower().isin(["true", "1"])
    df_p["kw_extended"] = df_p["kw_extended"].astype(str).str.lower().isin(["true", "1"])
    df_p = df_p[df_p["kw_extended"] & (df_p["role"] != "委員長報告") & (~df_p["exclude"])].copy()

    with groups_path.open("r", encoding="utf-8") as f:
        groups = json.load(f)

    speakers_map = {}
    for g_name, words in groups.items():
        g_id, _, _ = g_name.partition(" ")
        pattern = "|".join(words)
        sub = df_p[df_p["text"].str.contains(pattern, na=False, regex=True)]
        mem = sub[sub["role"] == "議員"]
        parties_speakers = {}
        for party, grp in mem.groupby("party"):
            parties_speakers[party] = grp["speaker"].value_counts().index.tolist()
        speakers_map[g_id] = parties_speakers

    items = []
    for _, r in issues.iterrows():
        name = r["論点"]
        issue_id, _, label = name.partition(" ")
        parties = {}
        for m in re.finditer(r"(\S+?)(\d+)(?:\s|$)", str(r["政党別の発言者数"])):
            parties[m.group(1)] = int(m.group(2))
        b = blocks.loc[name] if name in blocks.index else None
        items.append({
            "id": issue_id,
            "label": label or issue_id,
            "member": {
                "speakers": int(r["議員の発言者"]),
                "paragraphs": int(r["議員段落"]),
                "top_speaker": r["議員の最多"],
                "top_share": float(r["最多の割合"]),
                "parties": parties,
                "party_speakers": speakers_map.get(issue_id, {}),
            },
            "gov": {
                "responses": int(b["答弁ブロック"]) if b is not None else 0,
                "paragraphs": int(r["政府段落"]),
            },
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": build_source_text(config, len(df_p)),
        "note": "論点は、議論の中に出てきた語の組み合わせによる独自の分類。1つの段落が複数の論点に入るため、論点間の合計はできない。政府の応答回数は、見出し文(「〜についてお尋ねがありました」)で区切った答弁のうち、その論点の語を含むものの数",
        "issues": items,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(items)}論点を {out_path} に書き出しました")
    for it in items:
        print(f"{it['id']} {it['label']}: 議員{it['member']['speakers']}人 / 政府{it['gov']['responses']}回")


if __name__ == "__main__":
    main()
