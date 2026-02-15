---
title: "Claude Codeの.claude設定を複数プロジェクトで共有する -- Git Subtree + symlink構成"
emoji: "🔧"
type: "tech"
topics: ["claudecode", "git", "開発環境"]
published: false
---

## やりたいこと

Claude Codeを複数のプロジェクトで使っていると、コマンドやスキルの定義が各プロジェクトにコピペで散らばっていく。修正があれば全プロジェクトを手作業で直す羽目になる。

これを解消するために、**共有したい`.claude`の中身を別リポジトリに切り出し**、各プロジェクトにはGit Subtreeで取り込む構成を採った。プロジェクト固有の設定はそのまま`.claude/`に置けるので、共通と固有が自然に共存する。

## 構成の全体像

```
プロジェクト/
├── .claude-shared/              # Git Subtreeで共有リポを配置
│   ├── commands/                # 共通コマンド（実ファイル）
│   ├── skills/                  # 共通スキル（実ファイル）
│   └── agents/                  # 共通エージェント（実ファイル）
├── .claude/                     # Claude Codeが認識するディレクトリ
│   ├── commands/
│   │   ├── spec-plan.md         # <- symlink（共通）
│   │   └── my-deploy.md         # <- 実ファイル（プロジェクト固有）
│   ├── skills/
│   │   ├── steering/            # <- symlink（共通）
│   │   └── local-qa/            # <- 実ファイル（プロジェクト固有）
│   ├── agents/
│   │   └── doc-reviewer.md      # <- symlink（共通）
│   └── settings.json            # プロジェクト固有の設定
└── Makefile                     # Subtree + symlink管理
```

仕組みは単純で、`.claude-shared/`に共有リポの実体を置き、`.claude/`の中からsymlinkで参照する。Claude Codeは`.claude/`だけを見るので、symlinkか実ファイルかは気にしない。Gitもsymlinkをそのままトラッキングしてくれる。

## なぜGit Subtreeか

Git Submoduleでもできるが、Subtreeを選んだ理由はいくつかある。

- `clone`しただけで全ファイルが揃う（Submoduleは`--recursive`が必要）
- 共有リポの変更をプロジェクト側でローカルに修正してコミットできる
- CIで追加の初期化ステップが不要
- 操作がシンプル

Submoduleは「参照」に近く、Subtreeは「コピーを取り込む」に近い。`.claude/`のような設定ファイル群は後者のほうが扱いやすかった。

## セットアップ手順

### 共有リポの準備

まず、共有したいコマンドやスキルを独立したリポジトリにまとめる。

```
claude-shared-config/
├── commands/
│   ├── spec-plan.md
│   └── add-feature.md
├── skills/
│   ├── steering/
│   │   └── SKILL.md
│   └── git-commit/
│       └── SKILL.md
└── agents/
    └── doc-reviewer.md
```

これを普通にGitリポジトリとして管理する。

### プロジェクトへの統合

プロジェクト側で以下を実行する。

```bash
# 1. Subtreeとして追加
git subtree add --prefix=.claude-shared \
  https://github.com/yourname/claude-shared-config.git main --squash

# 2. .claude/ のディレクトリ構造を作成
mkdir -p .claude/commands .claude/skills .claude/agents

# 3. symlinkを作成
for item in .claude-shared/commands/*; do
  name=$(basename "$item")
  [ ! -e ".claude/commands/$name" ] && ln -s "../../.claude-shared/commands/$name" ".claude/commands/$name"
done
# skills, agents も同様
```

手作業でsymlinkを張るのは面倒なので、Makefileにまとめておく。

```makefile
REPO_URL = https://github.com/yourname/claude-shared-config.git
BRANCH = main

claude-init:
	git subtree add --prefix=.claude-shared $(REPO_URL) $(BRANCH) --squash
	$(MAKE) claude-link

claude-update:
	git subtree pull --prefix=.claude-shared $(REPO_URL) $(BRANCH) --squash
	$(MAKE) claude-link

claude-link:
	@mkdir -p .claude/commands .claude/skills .claude/agents
	@for item in .claude-shared/commands/*; do \
	  name=$$(basename "$$item"); \
	  [ ! -e ".claude/commands/$$name" ] && ln -s "../../.claude-shared/commands/$$name" ".claude/commands/$$name" || true; \
	done
	@for item in .claude-shared/skills/*; do \
	  name=$$(basename "$$item"); \
	  [ ! -e ".claude/skills/$$name" ] && ln -s "../../.claude-shared/skills/$$name" ".claude/skills/$$name" || true; \
	done
	@for item in .claude-shared/agents/*; do \
	  name=$$(basename "$$item"); \
	  [ ! -e ".claude/agents/$$name" ] && ln -s "../../.claude-shared/agents/$$name" ".claude/agents/$$name" || true; \
	done

claude-clean:
	@find .claude/commands -type l -delete 2>/dev/null || true
	@find .claude/skills -type l -delete 2>/dev/null || true
	@find .claude/agents -type l -delete 2>/dev/null || true
```

`make claude-init` で初回セットアップ、`make claude-update` で共有リポの更新を取り込める。

### プロジェクト固有の設定を追加

`.claude/`に直接ファイルを置けば、それがプロジェクト固有の設定になる。

```bash
# プロジェクト固有のコマンドを追加
cat > .claude/commands/deploy.md << 'EOF'
このプロジェクト固有のデプロイコマンド
...
EOF

# settings.json はプロジェクトごとに異なる
cp .claude-shared/settings.example.json .claude/settings.json
```

`claude-link`は既存ファイルがあればsymlinkを作らないので、プロジェクト固有ファイルが勝手に上書きされることはない。同名ファイルを`.claude/`に実ファイルとして置けば、共有側を上書きする形にもなる。

## 運用の流れ

### 共有リポの更新を反映する

```bash
make claude-update
git add .claude-shared/ .claude/
git commit -m "chore: claude-shared-configを更新"
```

### 共有リポ側に修正をフィードバックする

プロジェクト側で共有コマンドを改善した場合、共有リポに還元できる。

```bash
# .claude-shared/ 内のファイルを編集してコミット
vim .claude-shared/commands/spec-plan.md
git add .claude-shared/
git commit -m "improve: spec-planの出力フォーマットを改善"

# 共有リポにpush
git subtree push --prefix=.claude-shared \
  https://github.com/yourname/claude-shared-config.git main
```

## symlinkで確認する

実際にsymlinkが正しく張られているかは`ls -la`で確認できる。

```bash
$ ls -la .claude/commands/
lrwxr-xr-x  spec-plan.md -> ../../.claude-shared/commands/spec-plan.md
lrwxr-xr-x  add-feature.md -> ../../.claude-shared/commands/add-feature.md
-rw-r--r--  deploy.md    # プロジェクト固有（実ファイル）
```

symlinkは`->`で参照先が表示されるので、どれが共有でどれが固有かひと目でわかる。

## この構成で得られたもの

実際にこの構成で複数のPythonプロジェクトを運用してみて、いくつか実感した利点がある。

**共有設定の一元管理**: コマンドやスキルのバグ修正・改善を共有リポで一度行えば、各プロジェクトで`make claude-update`するだけで反映される。以前はプロジェクトごとに同じ修正を繰り返していた。

**プロジェクト固有設定との共存**: `settings.json`やプロジェクト特有のコマンドは`.claude/`に直接置ける。共有と固有がディレクトリ上で明確に分かれるので、どのファイルがどちらに属するか迷わない。

**新規プロジェクトの立ち上げが速い**: `make claude-init`だけで共有設定が丸ごと入る。あとはプロジェクト固有の`settings.json`と`CLAUDE.md`を用意すれば開発を始められる。

## 注意点

- `.claude-shared/.gitignore`がプロジェクトの`.gitignore`と競合することがある。プロジェクトの`.gitignore`に`.claude-shared/.gitignore`を追加しておくとよい
- symlinkはWindowsで扱いが異なる。開発者全員がmacOS/Linuxなら問題ないが、Windowsユーザーがいる場合はGitの`core.symlinks`設定を確認する必要がある
- Subtreeのコミット履歴はプロジェクトのログに混ざる。`--squash`オプションで1コミットにまとめているが、それでも気になる場合がある

## まとめ

Claude Codeの`.claude`ディレクトリをGit Subtree + symlinkで管理する構成を紹介した。共有リポに共通設定を集約し、プロジェクト側では`.claude-shared/`経由のsymlinkと直接配置の実ファイルを共存させる。仕組み自体はシンプルで、Makefileに数個のターゲットを用意するだけで運用できる。

同じような設定の散在に困っている人は、試してみる価値はあると思う。
