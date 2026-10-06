import pandas as pd

df = pd.read_csv("data/labels/disagreements.csv")

# --- 立場の食い違い ---
st = df[df["h_stance"] != df["a_stance"]]
print(f"=== 立場の食い違い: {len(st)} 件 ===\n")
for _, r in st.iterrows():
    print(f"[{r['speechID']} / {r['para_id']}] 人間={r['h_stance']} AI={r['a_stance']} 確信度={r['ai_confidence']}")
    print("  AIの理由:", r["ai_note"])
    print("  人間のメモ:", r["note"] if pd.notna(r["note"]) else "(なし)")
    print("  本文:", str(r["text"])[:200])
    print()

# --- 論点の食い違い(立場は一致しているもののうち12件) ---
tp = df[df["h_stance"] == df["a_stance"]].head(12)
print(f"=== 論点の食い違い(一部): {len(tp)} 件 ===\n")
for _, r in tp.iterrows():
    print(f"[{r['speechID']} / {r['para_id']}] 人間={r['human_topics']} AI={r['ai_topics_norm']}")
    print("  本文:", str(r["text"])[:100])
    print()