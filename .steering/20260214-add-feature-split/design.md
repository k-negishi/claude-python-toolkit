# 設計書

## 実装アプローチ

### 1. 既存の `/add-feature` スキルの分析

現在の `/add-feature` スキルは以下の構造:
- ステップ1-4: 準備、プロジェクト理解、既存パターン調査、計画フェーズ (ステアリングファイル生成)
- ステップ5-8: 実装ループ、検証、テスト、振り返り

### 2. 分割戦略

#### `/plan` スキル
- 既存の `/add-feature` のステップ1-4を抽出
- 入力: 機能名 または GitHub issue URL
- 出力: `.steering/[日付]-[機能名]/` ディレクトリと3ファイル
- 対話的確認を可能にする

#### `/implement` スキル
- 既存の `/add-feature` のステップ5-8を抽出
- 入力: ステアリングディレクトリパス
- TDDサイクルを明示的に組み込む
- 出力: 実装完了 + テストパス

#### `/add-feature` スキル (ラッパー)
- `/plan` を実行
- `/implement` を実行
- 既存の動作を維持

### 3. TDDサイクルの組み込み

実装ループ (ステップ5) を以下のように変更:

1. **RED**: 失敗するテストを先に書く
   - タスクに対応するテストケースを `tests/` に追加
   - テストを実行して失敗を確認

2. **GREEN**: 最小限の実装でテストをパスさせる
   - 機能を実装
   - テストを実行してパスを確認

3. **REFACTOR**: コードを改善
   - コード品質を向上
   - テストが引き続きパスすることを確認

### 4. ファイル構成

```
~/.claude/skills/
├── plan.md (新規作成)
├── implement.md (新規作成)
└── add-feature.md (既存、内容を変更してラッパー化)
```

### 5. issue との紐付け

- `requirements.md` の冒頭に `## GitHub Issue` セクションを追加
- issue URL を記載
- `/plan` で issue URL が渡された場合、自動で `gh issue view` して内容を取得

## 変更ファイル

### 新規作成
1. `~/.claude/skills/plan.md` - ステアリングファイル作成スキル
2. `~/.claude/skills/implement.md` - TDD実装スキル

### 変更
1. `~/.claude/skills/add-feature.md` - ラッパースキルに変更

## 技術的な考慮事項

### issue URL の解析
- GitHub issue URL のパターン: `https://github.com/{owner}/{repo}/issues/{number}`
- `gh issue view {number}` で内容を取得
- タイトルから機能名を生成 (スペースをハイフンに変換、小文字化)

### TDDサイクルの実装
- 各タスクに対して RED → GREEN → REFACTOR を明示的に実行
- テスト実行結果をログに記録
- リファクタリング時も必ずテストを実行

### 後方互換性
- `/add-feature` の既存動作を完全に維持
- 内部実装を変更しても、ユーザー体験は変わらない
