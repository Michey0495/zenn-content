# note-post

Zenn記事をnote.comに自動投稿するスキル。

## 使用方法

```
/note-post <記事ファイル> [--publish]
```

### オプション

| オプション | 説明 |
|-----------|------|
| --publish | 即時公開（省略時は下書き保存） |

### 例

```bash
# 下書きとして保存
/note-post articles/minecraft-threejs-typescript.md

# 即時公開
/note-post articles/minecraft-threejs-typescript.md --publish
```

## 事前準備

### 1. 環境変数の設定

`.env`ファイルにnoteのログイン情報を設定：

```
NOTE_EMAIL=your-email@example.com
NOTE_PASSWORD=your-password
```

### 2. 初回ログイン

初回実行時にブラウザが開き、ログイン処理を行います。
ログイン成功後、Cookieが保存され、次回以降は自動ログインされます。

## 実行コマンド

```bash
# 下書き保存
npm run note:draft articles/minecraft-threejs-typescript.md

# 即時公開
npm run note:publish articles/minecraft-threejs-typescript.md
```

## 仕組み

1. Markdownファイルを読み込み
2. フロントマターからタイトル・タグを抽出
3. Zenn独自記法（:::message等）を除去
4. Playwrightでnote.comにログイン
5. 新規記事ページを開く
6. タイトル・本文・タグを入力
7. 下書き保存または公開

## 注意事項

- noteの仕様変更により動作しなくなる可能性あり
- 画像は自動アップロードされない（Markdown内のURLはそのまま）
- headless: falseで実行するため、ブラウザが表示される
- 2段階認証は未対応

## トラブルシューティング

### ログインできない

1. `.env`の認証情報を確認
2. `scripts/.note-cookies.json`を削除して再実行
3. 2段階認証が有効なら無効化

### 投稿に失敗する

1. noteの仕様変更を確認
2. ブラウザの動作を目視で確認
3. セレクタが変わっている可能性あり
