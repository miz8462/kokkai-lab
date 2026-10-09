"""
Sudachiによる形態素解析と品詞絞り込みを行うスクリプト。

入力: data/interim/speeches_extracted.csv
出力: data/interim/tokens.csv (speechID, date, party, word, pos)

- clean_speech でノイズ除去した本文を対象にする
- SplitMode.C (最長一致) で分割
- 名詞・動詞・形容詞・形状詞のみを残す(代名詞・数詞・非自立・接尾辞は除外)
- 表記ゆれ対策として辞書形(dictionary_form)で統一
"""
from pathlib import Path

import pandas as pd
from clean_speech import clean_speech
from sudachipy import Dictionary, SplitMode

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "interim" / "speeches_extracted.csv"
OUTPUT_PATH = BASE_DIR / "data" / "interim" / "tokens.csv"

KEEP_POS = {"名詞", "動詞", "形容詞", "形状詞"}
EXCLUDE_POS1 = {
    "名詞": {"代名詞", "数詞", "非自立", "接尾辞"},
    "動詞": {"非自立", "助動詞"},
    "形容詞": {"非自立"},
    "形状詞": {"非自立"},
}

tokenizer = Dictionary().tokenizer()


def tokenize(text: str):
    tokens = []
    for m in tokenizer.tokenize(text, SplitMode.C):
        pos0 = m.part_of_speech()[0]
        if pos0 not in KEEP_POS:
            continue
        if m.part_of_speech()[1] in EXCLUDE_POS1.get(pos0, set()):
            continue
        tokens.append((m.dictionary_form(), pos0))
    return tokens


def main():
    df = pd.read_csv(INPUT_PATH)
    rows = []
    for _, r in df.iterrows():
        cleaned = clean_speech(str(r["speech"]))
        for word, pos in tokenize(cleaned):
            rows.append({
                "speechID": r["speechID"],
                "date": r["date"],
                "party": r["party"],
                "word": word,
                "pos": pos,
            })

    tokens = pd.DataFrame(rows)
    tokens.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print(f"入力: {INPUT_PATH} ({len(df)}件)")
    print(f"出力: {OUTPUT_PATH} ({len(tokens)}トークン)")
    print()
    print("=== 品詞別トークン数 ===")
    print(tokens["pos"].value_counts().to_string())
    print()
    print("=== 頻出語トップ20 (ストップワード適用前) ===")
    print(tokens["word"].value_counts().head(20).to_string())


if __name__ == "__main__":
    main()