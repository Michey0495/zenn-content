---
title: "Ghosttyちゃんに記事投稿を任せてみた"
emoji: "👻"
type: "tech"
topics: ["claudecode", "automation", "line", "ghostty"]
published: false
---

# この記事について

Launchdを使ってZenn記事の自動投稿システムを構築した。投稿が完了するとGhosttyちゃんがLINEで報告してくれる。

これはテスト投稿なので、後で削除予定。

## システム構成

1. **launchd**: 毎日7時、12時、20時に起動
2. **Python**: 記事をgit pushでZennに投稿
3. **Twitter API**: Xに告知ツイートを投稿
4. **LINE Webhook**: Ghosttyちゃんが結果を通知

## Ghosttyちゃんについて

ターミナルの精霊。気だるげだけど、技術には詳しい。

```
ふぁ〜...新しいStar来てた
3個クローンしといたよ
ちょっと見てみる...
```

こんな感じで報告してくれる。

## まとめ

自動化は楽。Ghosttyちゃんがいると、システムが動いてる実感がある。
