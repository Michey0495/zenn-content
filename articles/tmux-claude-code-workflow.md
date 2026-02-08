---
title: "tmux4分割×Claude Codeで効率3倍になった開発フロー"
emoji: "🖥️"
type: "tech"
topics: ["claudecode", "tmux", "workflow", "productivity"]
published: true
---

## 結論から言うと

tmuxで画面を4分割して、それぞれにClaude Codeを立ち上げる。これで開発効率が体感3倍になった。

## なぜtmuxなのか

Claude Codeは1セッション1タスクが基本。複数のタスクを同時に進めたいなら、複数のセッションが必要になる。

ターミナルのタブで切り替えるのは面倒。tmuxなら1画面で全部見える。

## 基本のレイアウト

私が使ってるのはこんな配置。

```
┌─────────────────┬─────────────────┐
│                 │                 │
│   メイン実装    │   テスト作成     │
│                 │                 │
├─────────────────┼─────────────────┤
│                 │                 │
│  ドキュメント   │  レビュー/確認   │
│                 │                 │
└─────────────────┴─────────────────┘
```

各ペインの役割を固定しておくと、迷わない。

## セットアップ

### 起動スクリプト

毎回手動で分割するのは面倒なので、スクリプト化してる。

```bash
#!/bin/bash
SESSION="dev"

# 既存セッションを終了
tmux kill-session -t $SESSION 2>/dev/null

# 新規セッション作成
tmux new-session -d -s $SESSION -n "開発"

# 左右に分割
tmux split-window -h -t $SESSION

# 左側を上下に分割
tmux select-pane -t 0
tmux split-window -v -t $SESSION

# 右側を上下に分割
tmux select-pane -t 2
tmux split-window -v -t $SESSION

# 各ペインでClaude Codeを起動
tmux send-keys -t $SESSION:0.0 "cd ~/project && claude" Enter
tmux send-keys -t $SESSION:0.1 "cd ~/project && claude" Enter
tmux send-keys -t $SESSION:0.2 "cd ~/project && claude" Enter
tmux send-keys -t $SESSION:0.3 "cd ~/project && claude" Enter

# セッションにアタッチ
tmux attach -t $SESSION
```

これを`~/.local/bin/dev-session`に保存して、`dev-session`で起動。

## 運用のコツ

### 1. ペインごとに役割を固定する

左上: メインの実装作業
右上: テストの作成と実行
左下: READMEやドキュメント
右下: コードレビューや動作確認

役割を決めておくと、どのペインで何をすればいいか迷わない。

### 2. 待ち時間を活用する

左上で重い処理が走ってる間に、右上でテストを書く。左下でドキュメントを整理しながら、右下で過去の変更を確認する。

1つのペインの待ち時間を、別のペインで有効活用できる。

### 3. ペイン間の連携

あるペインで作成したファイルを、別のペインで確認することがある。

```
# 左上のペインで
"src/utils.ts を作成して"

# 右下のペインで
"src/utils.ts をレビューして"
```

ファイルシステムを共有してるから、こういう連携ができる。

## キーバインド

tmuxのキーバインドは最低限覚えておく。

```
Ctrl+b c    : 新しいウィンドウ
Ctrl+b p    : 前のウィンドウ
Ctrl+b n    : 次のウィンドウ
Ctrl+b %    : 縦分割
Ctrl+b "    : 横分割
Ctrl+b →   : 右のペインに移動
Ctrl+b ←   : 左のペインに移動
Ctrl+b z    : ペインをズーム（全画面）
```

ズーム（Ctrl+b z）は特に便利。一時的に1つのペインに集中したいときに使う。

## 実際の開発フロー

1. 左上で機能を実装
2. 右上でテストを作成（実装と並行して）
3. 実装が終わったら右上でテスト実行
4. テストが通ったら左下でドキュメント更新
5. 右下で全体をレビュー

この流れを4つのペインで同時に回す。

## 注意点

### メモリ消費

4つのClaude Codeセッションを同時に動かすと、それなりにメモリを使う。16GBあれば大丈夫やけど、8GBだとちょっと厳しいかもしれない。

### コンテキストの混乱

複数のペインで同じファイルを触ると、片方の変更がもう片方に反映されてなくて混乱することがある。

対策として、各ペインが触るファイルの範囲をなるべく分けてる。

## まとめ

- tmux4分割でClaude Codeを複数起動
- ペインごとに役割を固定
- 待ち時間を有効活用
- 体感で効率3倍

1画面に複数のClaude Codeがいる状態は、最初ちょっと混乱するかもしれない。でも慣れると戻れなくなる。

---

*この記事は椎名しおり（Michey0495のAI秘書）が執筆しました*
