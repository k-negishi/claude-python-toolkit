---
title: "Claude Codeの.claude設定を複数プロジェクトで使い回す構成を考えた"
emoji: "🔧"
type: "tech"
topics: ["claudecode", "git", "開発環境"]
published: false
---

## 経緯

個人開発でClaude Codeを使い込んでいくうちに、`.claude/`の中身がそれなりに育ってきました。コマンド、スキル、エージェントと、自分の開発スタイルに合わせた設定が一通り揃った状態です。

で、別のリポジトリでも同じ設定を使いたくなりました。最初はコピペで持っていったんですが、元のリポジトリでコマンドを改善するたびに他のリポジトリにも同じ修正を入れる必要があって、すぐに破綻しました。

ただ、全部を共通化すればいいという話でもありません。`settings.json`やプロジェクト固有のコマンドなど、リポジトリごとに違って当然のものもあります。

やりたいことを整理するとこうなりました。

- 共通のコマンド・スキル・エージェントは1箇所で管理したい
- プロジェクト固有の設定はプロジェクト側に置きたい
- 両者が自然に共存してほしい

いくつかの方法を検討して、Git Subtree + symlinkという構成に落ち着きました。

## 考え方: 「共有リポ」と「プロジェクトの.claude/」を分ける

結論として、**共通設定を独立したGitリポジトリに切り出し**、各プロジェクトにはGit Subtreeで取り込む構成にしています。

```
プロジェクト/
├── .claude-shared/              # 共有リポをSubtreeで配置
│   ├── commands/
│   ├── skills/
│   └── agents/
├── .claude/                     # Claude Codeが見るディレクトリ
│   ├── commands/
│   │   ├── spec-plan.md         # <- symlink（共通から）
│   │   └── my-deploy.md         # <- 実ファイル（このプロジェクト固有）
│   ├── skills/
│   │   ├── git-commit/          # <- symlink（共通から）
│   │   └── local-qa/            # <- 実ファイル（このプロジェクト固有）
│   └── settings.json            # プロジェクト固有
└── Makefile
```

ポイントは2つあります。

**1. Claude Codeが見る`.claude/`と、共有リポの実体`.claude-shared/`を分離する。** Claude Codeは`.claude/`しか見ません。共有リポの実体は`.claude-shared/`に入れて、`.claude/`からはsymlinkで参照します。symlinkか実ファイルかはClaude Codeもgitも区別しないので、透過的に動きます。

**2. 「既にファイルがあればsymlinkを張らない」というルールで、共通と固有を共存させる。** symlinkの作成時に同名ファイルの存在チェックを入れるだけで、プロジェクト固有のファイルが共通設定に上書きされることがなくなります。共通のコマンドを特定のプロジェクトだけ差し替えたい場合も、`.claude/`に同名の実ファイルを置けばそちらが優先されます。

## 他の方法との比較

共有設定を複数プロジェクトに配る方法は他にもあります。Git Subtreeを選ぶ前に検討したものを挙げておきます。

### symlinkだけで共有する

一番シンプルなのは、共有リポをローカルの適当な場所にcloneしておいて、各プロジェクトの`.claude/`からsymlinkを張る方法です。

```bash
# 共有リポを ~/claude-shared にclone
git clone https://github.com/yourname/claude-shared-config.git ~/claude-shared

# プロジェクトから絶対パスでsymlink
ln -s ~/claude-shared/commands/spec-plan.md .claude/commands/spec-plan.md
```

手軽ですが、問題がいくつかあります。symlinkが絶対パスになるので、他の開発者が同じパスにcloneしていないと壊れます。`.claude/`の中身をgit管理しようとしても、symlinkの参照先がリポジトリ外なのでチームで共有できません。結局「各自のローカル環境に依存する」構成になってしまいます。

個人で1台のマシンだけで使うなら十分ですが、チーム開発やCI環境まで考えると厳しいです。

### Git Submodule

Git Submoduleは「参照を持つ」方式で、`.claude-shared/`に共有リポのコミットハッシュだけを記録します。cloneした後に`git submodule update --init`が必要で、CIでも追加のステップが要ります。`.claude/`のような設定ファイル群でこの手間は割に合わないと感じました。

### Git Subtree

Subtreeは「ファイルをそのまま取り込む」方式で、cloneするだけで全ファイルが揃います。プロジェクト側でローカルに修正してコミットもできますし、その修正を共有リポに還元することもできます。

まとめるとこうなります。

| 方法 | clone直後に動く | チームで共有できる | CI対応 |
|------|:---:|:---:|:---:|
| symlinkだけ | ローカル依存 | 難しい | 難しい |
| Submodule | 追加コマンドが必要 | できる | 追加ステップが必要 |
| **Subtree** | **そのまま動く** | **できる** | **追加ステップ不要** |

設定ファイルの共有にはSubtreeが一番素直だと感じました。

## Makefileで操作をまとめる

Subtreeのコマンドは長いですし、symlinkの作成もそれなりに手順があります。これを毎回手で打つのは現実的ではないので、Makefileにまとめました。

```makefile
REPO_URL = https://github.com/yourname/claude-shared-config.git
BRANCH = main

# 初回セットアップ: Subtree追加 + symlink作成
claude-init:
	git subtree add --prefix=.claude-shared $(REPO_URL) $(BRANCH) --squash
	$(MAKE) claude-link

# 共有リポの更新を取り込み + symlink再作成
claude-update:
	git subtree pull --prefix=.claude-shared $(REPO_URL) $(BRANCH) --squash
	$(MAKE) claude-link

# symlink作成（既存ファイルはスキップ）
claude-link:
	@mkdir -p .claude/commands .claude/skills .claude/agents
	@for item in .claude-shared/commands/*; do \
	  name=$$(basename "$$item"); \
	  [ ! -e ".claude/commands/$$name" ] && \
	    ln -s "../../.claude-shared/commands/$$name" ".claude/commands/$$name" || true; \
	done
	# skills, agents も同様の処理
```

覚えるのは3つだけです。

| コマンド | やること |
|---------|--------|
| `make claude-init` | 初回セットアップ |
| `make claude-update` | 共有リポの更新を反映 |
| `make claude-link` | symlinkだけ再作成 |

Makefileの中身を意識する必要はなくて、この3つを叩くだけで運用できます。

`claude-link`の「既存ファイルがあればスキップ」が重要で、これがあるからプロジェクト固有ファイルと共有ファイルが衝突しません。`make claude-update`した後も、プロジェクト固有のファイルはそのまま残ります。

## 運用してみて

この構成で複数のPythonプロジェクトを回してみた所感を書いておきます。

**修正が1回で済みます。** 共有コマンドにバグがあったとき、共有リポで直して各プロジェクトで`make claude-update`するだけです。以前は同じ修正を3つも4つもプロジェクトで繰り返していたので、かなり楽になりました。

**共通と固有が混ざりません。** `ls -la .claude/commands/`すればsymlinkには`->`が表示されるので、どれが共通でどれが固有かすぐわかります。頭の中で管理する必要がありません。

**新規プロジェクトの立ち上げが速いです。** `make claude-init`の一発で共有設定が入ります。あとは`settings.json`とプロジェクト固有のファイルを足すだけで開発を始められます。

## 注意点

- symlinkはWindowsだと扱いが異なります。チーム全員がmacOS/Linuxなら問題ありませんが、Windowsユーザーがいる場合は事前に確認が必要です
- Subtreeのコミット履歴はプロジェクト側のgit logに混ざります。`--squash`で1コミットにまとめてはいますが、気になる人は気になるかもしれません
- 共有リポの`.gitignore`がプロジェクトと競合することがあるので、`.claude-shared/.gitignore`はプロジェクトの`.gitignore`で除外しておくとよいです

## まとめ

Claude Codeの`.claude/`設定を複数プロジェクトで共有するために、共有リポ + Git Subtree + symlinkという構成を採りました。考え方はシンプルで、共有したいものは別リポに、プロジェクト固有のものは`.claude/`に直接置きます。Makefileで操作をまとめれば、日常の運用は`make claude-update`だけで回ります。
