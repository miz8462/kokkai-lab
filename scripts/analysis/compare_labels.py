import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

# 使い方: python scripts/analysis/compare_labels.py [人間のラベルのCSV] [AIのラベルのCSV]
GOLD = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/labels/gold_sheet.csv")
AI = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/labels/ai_labels.csv")
OUT = Path(f"data/labels/disagreements_{GOLD.stem}.csv")  # 食い違いの一覧(出力)

STANCE_JP = {
    "減税・廃止": "a", "現行維持": "b", "引き上げ": "c",
    "条件付き・不明確": "d", "該当なし": "e",
}
TOPIC_JP = {
    "物価高・家計": "f", "社会保障財源": "g", "財政規律": "h",
    "逆進性・格差": "i", "中小企業・インボイス": "j", "景気・成長": "k",
    "その他": "l",
}


def norm(s) -> str:
    """全角→半角、前後の空白除去、小文字化でそろえる。"""
    if pd.isna(s):
        return ""
    return unicodedata.normalize("NFKC", str(s)).strip().lower()


STANCE_MAP = {norm(k): v for k, v in STANCE_JP.items()}
TOPIC_MAP = {norm(k): v for k, v in TOPIC_JP.items()}


def norm_stance(s) -> str:
    v = norm(s)
    return STANCE_MAP.get(v, v)


def norm_topics(s) -> frozenset:
    v = norm(s)
    tokens = [t.strip() for t in re.split(r"[;,、]", v) if t.strip()]
    return frozenset(TOPIC_MAP.get(t, t) for t in tokens)


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


if not GOLD.exists():
    raise SystemExit(f"{GOLD} がありません。")
if not AI.exists():
    raise SystemExit(f"{AI} がありません。先にZedのエージェントでAIのラベルを作ってください。")

gold = pd.read_csv(GOLD, encoding="utf-8-sig")
ai = pd.read_csv(AI, encoding="utf-8-sig")

# AIの出力に同じ段落が重複していたら、後のものを使う
ai = ai.drop_duplicates(["speechID", "para_id"], keep="last")

# 突き合わせ(speechIDとpara_idの組で結合)
m = gold.merge(ai, on=["speechID", "para_id"], how="left")

m["h_stance"] = m["stance"].map(norm_stance)
m["a_stance"] = m["ai_stance"].map(norm_stance)

# 論点は、人間側とAI側の両方に列があるときだけ比べる
has_topics = "topics" in m.columns and "ai_topics" in m.columns
if has_topics:
    m["h_topics"] = m["topics"].map(norm_topics)
    m["a_topics"] = m["ai_topics"].map(norm_topics)

print(f"人間のラベル: {GOLD}")
print(f"AIのラベル: {AI}")
print(f"人間のラベルが未入力: {(m['h_stance'] == '').sum()} 件")
print(f"AIのラベルがない: {(m['a_stance'] == '').sum()} 件")

# 両方そろっている行だけで比べる
both = m[(m["h_stance"] != "") & (m["a_stance"] != "")].copy()
n = len(both)
print(f"比較できる段落: {n} 件\n")
if n == 0:
    raise SystemExit("比較できる段落がありません。")

# --- 立場(stance) ---
both["stance_ok"] = both["h_stance"] == both["a_stance"]
print("【立場】一致率:", f"{both['stance_ok'].mean():.1%}", f"({both['stance_ok'].sum()}/{n})")
print("凡例: a=減税・廃止 b=現行維持 c=引き上げ d=条件付き・不明確 e=該当なし")
print("行=人間、列=AI")
print(pd.crosstab(both["h_stance"], both["a_stance"]), "\n")

# AIの確信度ごとの一致率(確信度が当てになるかの確認)
if "ai_confidence" in both.columns:
    print("AIの確信度別の立場の一致率:")
    print(both.groupby("ai_confidence")["stance_ok"].agg(["mean", "count"]), "\n")

# --- 論点(topics) ---
if has_topics:
    both["topics_exact"] = both["h_topics"] == both["a_topics"]
    both["topics_jaccard"] = [jaccard(h, a) for h, a in zip(both["h_topics"], both["a_topics"])]
    both["topics_overlap"] = [bool(h & a) for h, a in zip(both["h_topics"], both["a_topics"])]
    print("【論点】完全一致率:", f"{both['topics_exact'].mean():.1%}")
    print("【論点】1つ以上共通:", f"{both['topics_overlap'].mean():.1%}")
    print("【論点】平均Jaccard係数:", f"{both['topics_jaccard'].mean():.2f}\n")
else:
    print("【論点】人間側に topics 列がないため、比較を省略しました\n")

# --- 食い違いの一覧を書き出す ---
if has_topics:
    mismatch = ~both["stance_ok"] | ~both["topics_exact"]
else:
    mismatch = ~both["stance_ok"]
diff = both[mismatch].copy()

cols = ["speechID", "para_id", "h_stance", "a_stance", "ai_confidence", "note", "ai_note", "text"]
if has_topics:
    diff["human_topics"] = [";".join(sorted(s)) for s in diff["h_topics"]]
    diff["ai_topics_norm"] = [";".join(sorted(s)) for s in diff["a_topics"]]
    cols += ["human_topics", "ai_topics_norm"]
diff[[c for c in cols if c in diff.columns]].to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"食い違い {len(diff)} 件を {OUT} に書き出しました")
