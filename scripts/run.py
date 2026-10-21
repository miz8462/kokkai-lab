"""
run.py — 前処理から記事データ生成までを一括実行する入口スクリプト

引数:
  --slug (必須): 分析対象のスラッグ
  --fetch (任意): fetch_speeches.py を実行する
  --force (任意): --fetch と一緒のときだけ有効。fetch_speeches.py に --force を渡す

実行順:
  1. (--fetch のときだけ) fetch_speeches.py
  2. extract_fields.py
  3. split_paragraphs.py
  4. mark_roles.py
  5. dedupe_paragraphs.py
  6. (語群ファイルの確認)
  7. issue_groups.py
  8. answer_blocks.py
  9. build_article_data.py

使い方:
  python scripts/run.py --slug consumption-tax-issues
  python scripts/run.py --slug consumption-tax-issues --fetch
  python scripts/run.py --slug consumption-tax-issues --fetch --force
"""
import argparse
import subprocess
import sys
from pathlib import Path

# scripts/ を sys.path に追加して common を import 可能にする
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from common import paths  # noqa: E402


def run_step(script_path: Path, slug: str, extra_args: list[str] | None = None) -> int:
    """サブプロセスとしてスクリプトを実行し、終了コードを返す"""
    cmd = [sys.executable, str(script_path), "--slug", slug]
    if extra_args:
        cmd.extend(extra_args)
    result = subprocess.run(cmd)
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="前処理から記事データ生成までを一括実行する入口スクリプト"
    )
    parser.add_argument("--slug", required=True, help="分析対象のスラッグ (例: consumption-tax-issues)")
    parser.add_argument("--fetch", action="store_true", help="fetch_speeches.py を実行する")
    parser.add_argument("--force", action="store_true", help="--fetch と一緒のときだけ有効。fetch_speeches.py に --force を渡す")
    args = parser.parse_args()

    slug: str = args.slug
    fetch: bool = args.fetch
    force: bool = args.force

    # 生データのフォルダが存在するか確認 (--fetch のときは skip)
    if not fetch:
        p = paths(slug)
        raw_path = p["raw"]
        if not raw_path.exists():
            print(f"生データのフォルダがありません: {raw_path}。--slug の綴りを確認するか、--fetch を付けて取得してください。")
            sys.exit(1)

    scripts_dir = Path(__file__).resolve().parent
    steps: list[tuple[str, Path, list[str] | None]] = []

    # ステップの定義 (名前, スクリプトパス, 追加引数)
    if fetch:
        fetch_args = ["--force"] if force else None
        steps.append(("fetch_speeches", scripts_dir / "data" / "fetch_speeches.py", fetch_args))

    steps.extend([
        ("extract_fields", scripts_dir / "data" / "extract_fields.py", None),
        ("split_paragraphs", scripts_dir / "data" / "split_paragraphs.py", None),
        ("mark_roles", scripts_dir / "data" / "mark_roles.py", None),
        ("dedupe_paragraphs", scripts_dir / "data" / "dedupe_paragraphs.py", None),
    ])

    # 語群ファイルの確認 (dedupe_paragraphs と issue_groups の間)
    p = paths(slug)
    groups_path = p["groups"]
    if not groups_path.exists():
        print(f"語群ファイルがありません: {groups_path}。ここまでの前処理は完了しています。語群を作ってから再実行してください。")
        sys.exit(1)

    steps.extend([
        ("issue_groups", scripts_dir / "analysis" / "issue_groups.py", None),
        ("answer_blocks", scripts_dir / "analysis" / "answer_blocks.py", None),
        ("build_article_data", scripts_dir / "analysis" / "build_article_data.py", None),
    ])

    total = len(steps)
    for i, (name, script_path, extra_args) in enumerate(steps, start=1):
        print(f"[{i}/{total}] {name}")
        retcode = run_step(script_path, slug, extra_args)
        if retcode != 0:
            print(f"ステップ '{name}' が失敗しました (終了コード: {retcode})")
            sys.exit(retcode)

    print(f"全ステップ ({total}/{total}) が完了しました")


if __name__ == "__main__":
    main()
