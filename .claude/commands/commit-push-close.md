---
description: 変更をコミットし、リモートにpushし、GitHub issueをクローズする
argument-hint: issue番号（オプション）
---

# Commit, Push, Close コマンド

変更をコミットし、リモートにpushし、関連するGitHub issueをクローズする一連の操作を自動実行するコマンドです。

## 使い方

```bash
/commit-push-close [issue番号]
```

**引数**:
- `issue番号` (オプション): クローズするGitHub issueの番号。省略した場合は、その会話の中で対応していた issue があればその番号。なければクローズなしでコミットとpushのみ実行。

**例**:
```bash
/commit-push-close 17
# → commit → push → issue #17をクローズ

/commit-push-close
# → commit → push のみ（issueクローズなし）
# or
# → commit → push → 会話の中で対応していた issue があればその番号を自動的にクローズ
```

## 実行フロー

### ステップ1: Git Commit

`Skill('git-commit')` を呼び出してコミットを作成します。

- 変更内容を確認（`git status`, `git diff`）
- 適切なprefixを判定（add/fix/docs/refactor/test/chore/perf/build/ci/revert/style）
- コミットメッセージを作成・実行

### ステップ2: Git Push

リモートリポジトリ（main）にpushします。

```bash
git push origin main
```

### ステップ3: GitHub Issue Close（オプション）

引数で指定されたissue番号がある場合、`close-issue` スキルを使用してissueをクローズします。

```
Skill('close-issue', args='<issue番号>')
```

**close-issueスキルが自動的に行うこと**:
- 最新のコミット情報を取得
- ステアリングファイル名を記録（`.steering/[YYYYMMDD]-[タスク名]/`）
- 実装サマリを生成（変更内容、品質チェック結果）
- Issueにコメントを追加
- Issueをクローズ
- **クローズしたissueのURLを出力**

**⚠️ 重要**: close-issueスキルは、以下の形式でissueのURLを出力します:

```
✅ Issue Closed: https://github.com/<owner>/<repo>/issues/<番号>
```

例:
```
✅ Issue Closed: https://github.com/k-negishi/ai-curated-newsletter/issues/17
```

## 注意事項

- **コミット前の確認**: 必ず変更内容を確認してから実行してください
- **複数issue対応**: 1つのコミットが複数issueに関連する場合は、代表的なissue番号を指定してください
- **issueクローズのタイミング**: issue番号を指定した場合、必ずpush後にクローズされます
- **リモートブランチ**: デフォルトで `main` ブランチにpushします
- **URL出力**: issueをクローズした場合、必ずそのURLを出力します

## 失敗時の対処

### コミットが失敗した場合
- `git status` で変更内容を確認
- 必要に応じてファイルをステージング（`git add`）
- コミットメッセージを見直して再実行

### Pushが失敗した場合
- リモートとの競合を確認（`git pull --rebase`）
- 認証情報を確認
- ネットワーク接続を確認

### Issue Closeが失敗した場合
- issue番号が正しいか確認
- `gh` コマンドの認証状態を確認（`gh auth status`）
- 手動でissueをクローズすることも可能

## 関連コマンド

- `/git-commit`: コミットのみ実行
- `git push`: pushのみ実行
- `gh issue close <番号>`: issueクローズのみ実行

## ベストプラクティス

1. **作業単位でコミット**: 1つの機能・修正ごとにこのコマンドを実行
2. **issue番号の記録**: コミットメッセージにissue番号を含める習慣をつける
3. **テスト実行後に実行**: 必ずテストがパスしてからコミット・push
4. **振り返りを記録**: ステアリングファイルの振り返りセクションを更新してから実行

## 実装の流れ（内部処理）

```text
1. Skill('git-commit') を実行
   ↓
2. git push origin main を実行
   ↓
3. [issue番号が指定されている場合]
   Skill('close-issue', args='<issue番号>') を実行
   - 最新のコミット情報を取得
   - ステアリングファイル名を記録
   - 実装サマリを生成
   - Issueにコメントを追加
   - Issueをクローズ
   - issueのURLを出力
   ↓
4. 完了報告
```

## 例: issue #17のクローズ

```bash
/commit-push-close 17
```

実行結果:
```
✅ Commit: add: メール本文に公開日を追加し体裁を改善
✅ Push: リモートリポジトリ（main）にpush完了

### GitHub Issue更新
- ✅ コメント追加: https://github.com/k-negishi/ai-curated-newsletter/issues/17#issuecomment-xxx
- ✅ Issue #17クローズ: メールの体裁変更

### 実装サマリ
- コミット: 5bae879
- ステアリングファイル: .steering/20260215-メールの体裁変更/
- 変更ファイル: 13 files
- 品質チェック: 全てパス

✅ Issue Closed: https://github.com/k-negishi/ai-curated-newsletter/issues/17

すべての作業が正常に完了しました。
```
