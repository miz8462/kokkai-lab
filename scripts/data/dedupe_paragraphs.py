"""
dedupe_paragraphs.py — 議長の議事進行と、同じ文面の再掲を分析対象から外すスクリプト

目的:
  paragraphs_roles.csv に exclude / exclude_reason 列を加えて、
  paragraphs_clean.csv を作る。行は削除しない(前後の段落の文脈を残すため)。
  除外するもの:
    1. role が「議長」の段落(議事進行で、論点の発言ではない)
    2. 同じ日・同じ発言者で、文面がほぼ同一の段落(例: 衆参で読まれた同一の演説)。
       最初の1件を残し、2件目以降を除外する。
       短い段落(既定40字未満)は「お尋ねがありました」などの定型句なので対象外。

使い方:
  python scripts/data/dedupe_paragraphs.py          # 類似度の閾値 0.9
  python scripts/data/dedupe_paragraphs.py 0.95     # 閾値を指定

入力:
  data/interim/paragraphs_roles.csv
出力:
  data/interim/paragraphs_clean.csv
  output/duplicates.md  (どの段落をどれの重複とみなしたかの一覧)
"""
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "data/interim/paragraphs_roles.csv"
DST = ROOT / "data/interim/paragraphs_clean.csv"
REPORT = ROOT / "output/duplicates.md"

THRESHOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 0.9
MIN_LEN = 40


def normalize(s: str) -> str:
    """句読点・空白・括弧を除いて、表記ゆれの差を小さくする"""
    return re.sub(r"[\s、。,.・()（）「」『』]", "", s)


df = pd.read_csv(SRC)
df["text"] = df["text"].fillna("")
df["exclude"] = False
df["exclude_reason"] = ""

# 1. 議長
is_chair = df["role"] == "議長"
df.loc[is_chair, "exclude"] = True
df.loc[is_chair, "exclude_reason"] = "議長(議事進行)"

# 2. 同じ日・同じ発言者での再掲
df["_norm"] = df["text"].map(normalize)
pairs = []
candidates = df[(~df["exclude"]) & (df["_norm"].str.len() >= MIN_LEN)]
for (_date, _speaker, _sid), grp in candidates.groupby(["date", "speaker", "speechID"]):
    kept = []  # (index, norm)
    for idx, norm in zip(grp.index, grp["_norm"]):
        dup_of = None
        for k_idx, k_norm in kept:
            sm = SequenceMatcher(None, norm, k_norm, autojunk=False)
            if sm.real_quick_ratio() < THRESHOLD or sm.quick_ratio() < THRESHOLD:
                continue
            ratio = sm.ratio()
            if ratio >= THRESHOLD:
                dup_of = (k_idx, ratio)
                break
        if dup_of is None:
            kept.append((idx, norm))
        else:
            df.loc[idx, "exclude"] = True
            df.loc[idx, "exclude_reason"] = f"再掲(元: 行{dup_of[0]})"
            pairs.append((idx, dup_of[0], dup_of[1]))

# 3. 別の speechID でも、同じ日・同じ発言者で文面がほぼ同一(衆参で読まれた同一演説など)
# 別発言での再掲を認める日(衆参で同じ演説・報告が読まれた日)
CROSS_DATES = {"2026-02-20"}  # 施政方針演説
CROSS_THRESHOLD = 0.97
para_ids = df["para_id"].astype(int).to_dict()  # {行番号: para_id}
cross_pairs = []
cands = df[(~df["exclude"]) & (df["_norm"].str.len() >= MIN_LEN)]
for (_date, _speaker), grp in cands.groupby(["date", "speaker"]):
    kept = []  # (index, norm, speechID)
    for idx, norm, sid in zip(grp.index, grp["_norm"], grp["speechID"]):
        dup_of = None
        for k_idx, k_norm, k_sid in kept:
            if k_sid == sid:
                continue
            if str(_date) not in CROSS_DATES:
                continue
            sm = SequenceMatcher(None, norm, k_norm, autojunk=False)
            thr = 0.9 if str(_date) in CROSS_DATES else CROSS_THRESHOLD
            if sm.real_quick_ratio() < thr or sm.quick_ratio() < thr:
                continue
            ratio = sm.ratio()
            if ratio >= (0.9 if str(_date) in CROSS_DATES else CROSS_THRESHOLD):
                dup_of = (k_idx, ratio)
                break
        if dup_of is None:
            kept.append((idx, norm, sid))
        else:
            df.loc[idx, "exclude"] = True
            df.loc[idx, "exclude_reason"] = f"別発言での再掲(元: 行{dup_of[0]})"
            cross_pairs.append((idx, dup_of[0], dup_of[1]))

df = df.drop(columns=["_norm"])
DST.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(DST, index=False, encoding="utf-8-sig")

# レポート
lines = [f"# 再掲とみなした段落(閾値 {THRESHOLD}、{len(pairs)}件)\n"]
for idx, orig, ratio in pairs:
    r, o = df.loc[idx], df.loc[orig]
    lines.append(f"- {r['date']} {r['speaker']} 類似度{ratio:.3f}")
    lines.append(f"  - 除外(行{idx}): {r['text'][:60]}…")
    lines.append(f"  - 残す(行{orig}): {o['text'][:60]}…")
REPORT.parent.mkdir(exist_ok=True)
REPORT.write_text("\n".join(lines), encoding="utf-8")

# 集計
print(f"全段落: {len(df)}")
print("除外(全段落):", df["exclude"].sum(), "行")
kinds = df.loc[df["exclude"], "exclude_reason"].str.extract(r"^(議長|別発言での再掲|再掲)")[0]
print("  内訳:", " / ".join(f"{k} {n}" for k, n in kinds.value_counts().items()))
for col, label in [("has_keyword", "消費税を含む"), ("kw_extended", "拡張語を含む")]:
    m = df[col].astype(str).str.lower().isin(["true", "1"])
    t = df[m & (df["role"] != "委員長報告")]
    print(f"{label}対象: {len(t)} → 除外後 {int((~t['exclude']).sum())}(除外 {int(t['exclude'].sum())})")
print(f"{DST} と {REPORT} に書き出しました")
