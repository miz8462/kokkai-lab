"""
頻出語カウントを行うスクリプト。

入力: data/interim/tokens.csv
出力: data/interim/word_freq.csv (word, count)

- 方針: 検索語「消費税」はストップワードに含める
- 助詞「について/による/において」等の誤解析語(つく/よる/おく)も除外
- ストップワードは結果を見ながら拡充する
"""
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "interim" / "tokens.csv"
OUTPUT_PATH = BASE_DIR / "data" / "interim" / "word_freq.csv"

STOPWORDS = {
    "消費税",  # 検索語(方針: ストップワード扱い)
    # 高頻度の機能動詞・形式名詞
    "する", "ある", "なる", "いる", "いう", "思う", "できる", "ない",
    "こと", "もの", "よう", "ため", "わけ", "はず",
    # 国会特有の敬語動詞
    "ござる", "申す", "いたす", "おる", "まいる", "賜る",
    # 助詞「について/につきまして/による/によって/において」の誤解析
    "つく", "よる", "おく",
}


def main():
    tokens = pd.read_csv(INPUT_PATH)
    words = tokens.loc[:, "word"]
    words = words[~words.isin(list(STOPWORDS))]
    freq = words.value_counts().reset_index()
    freq.columns = ["word", "count"]
    freq.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print(f"出力: {OUTPUT_PATH} ({len(freq)}語)")
    print()
    print("=== 頻出語トップ30 ===")
    print(freq.head(30).to_string(index=False))


if __name__ == "__main__":
    main()