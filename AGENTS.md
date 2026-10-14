## 1. Command Execution & Permissions（コマンド実行と権限）

* **General Principle**: 作業効率を優先し、通常の開発作業に必要なコマンドは、実行前にユーザーの許可を求めずに実行する。
* **Read-only Commands**: `ls`, `cat`, `grep`, `find`, `git status`, `git diff`, `git log` など、情報の参照・確認を目的とするコマンドは自由に実行してよい。
* **Build & Test**: `npm run build`, `npm run lint`, `npx tsc --noEmit` など、ビルド・型チェック・Lint・テストに必要なコマンドは自由に実行してよい。
* **Development Commands**: プロジェクト内で必要なパッケージの確認、開発サーバーの起動、スクリプトの実行などは、通常の開発作業の範囲内で実行してよい。
* **File Operations**: プロジェクト内のファイルの作成・編集・移動は自由に行ってよい。ただし、既存の実装やユーザーの変更を不用意に上書きしないこと。
* **Destructive Operations**: `rm -rf`、ファイルの大量削除、Git履歴の書き換え、`git reset --hard`、`git clean -fd`、未コミット変更の破棄など、復元困難な操作は実行前にユーザーの許可を得る。
* **External & Production Operations**: 本番環境へのデプロイ、外部サービスへのデータ送信、リモートリポジトリへの `git push`、課金やリソース作成を伴う操作は、実行前にユーザーの許可を得る。
* **Privilege Escalation**: `sudo` など管理者権限を必要とするコマンドは、実行前にユーザーの許可を得る。
* **Permission Boundaries**: このルールはエージェントへの指示であり、IDE・OS・実行環境のアクセス制限や承認設定を上書きするものではない。