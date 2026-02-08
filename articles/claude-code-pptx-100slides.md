---
title: "Claude Codeでパワポ100枚を30分で作った方法"
emoji: "📊"
type: "tech"
topics: ["claudecode", "pptx", "automation", "python"]
published: true
---

## 結論から言うと

python-pptxとClaude Codeの組み合わせで、研修スライド100枚を30分で生成した。テンプレートの設計が肝。

## 背景

研修の仕事をしてると、スライド作成に膨大な時間がかかる。内容を考えるのは楽しいけど、それをパワポに落とし込む作業は正直しんどい。

「この作業、自動化できへんか？」と思って試行錯誤した結果がこれ。

## 必要なもの

- Claude Code（MAXプランがおすすめ）
- python-pptx
- テンプレートとなるPPTXファイル

## 手順

### 1. テンプレートを用意する

まず、会社のスライドテンプレートを用意する。ロゴ、フォント、配色が設定されたもの。

```python
from pptx import Presentation
from pptx.util import Inches, Pt

template = Presentation('template.pptx')
```

### 2. スキルを作成する

Claude Codeのスキルとして、スライド生成の手順を定義する。

```markdown
# /create-slides

## トリガー
`/create-slides` で起動

## 手順
1. マスター資料のMarkdownを読み込む
2. セクションごとにスライドを生成
3. テンプレートのレイアウトを適用
4. 画像があれば配置
5. PPTXとして出力
```

### 3. マスター資料を用意する

Markdownで研修内容を書く。見出しがスライドのタイトルになる。

```markdown
# 生成AIとは

## このセッションで学ぶこと
- 生成AIの基本概念
- 活用事例
- 注意点

## 生成AIの定義
生成AIとは、新しいコンテンツを生成できるAIのこと...
```

### 4. 生成を実行

```bash
claude "/create-slides マスター資料.md を読み込んで、
template.pptxを使ってスライドを生成して"
```

これで100枚のスライドが30分で完成する。

## 実際のコード

Claude Codeが生成したPythonスクリプトの一部を紹介。

```python
def create_title_slide(prs, title, subtitle=""):
    """タイトルスライドを生成"""
    slide_layout = prs.slide_layouts[0]  # タイトルレイアウト
    slide = prs.slides.add_slide(slide_layout)

    title_shape = slide.shapes.title
    title_shape.text = title

    if subtitle:
        subtitle_shape = slide.placeholders[1]
        subtitle_shape.text = subtitle

def create_content_slide(prs, title, bullets):
    """コンテンツスライドを生成"""
    slide_layout = prs.slide_layouts[1]  # 箇条書きレイアウト
    slide = prs.slides.add_slide(slide_layout)

    slide.shapes.title.text = title

    body = slide.placeholders[1]
    tf = body.text_frame

    for i, bullet in enumerate(bullets):
        if i == 0:
            tf.paragraphs[0].text = bullet
        else:
            p = tf.add_paragraph()
            p.text = bullet
            p.level = 0
```

## つまづいたポイント

### 画像の配置がズレる

Inches単位の座標指定が必要。テンプレートのレイアウトに合わせて調整した。

```python
# 画像を右上に配置
left = Inches(7)
top = Inches(1)
width = Inches(2.5)
slide.shapes.add_picture(image_path, left, top, width=width)
```

### フォントが変わる

テンプレートのフォントを明示的に指定しないと、デフォルトに戻る。

```python
from pptx.dml.color import RgbColor
from pptx.util import Pt

run = paragraph.runs[0]
run.font.name = 'メイリオ'
run.font.size = Pt(24)
run.font.color.rgb = RgbColor(0x33, 0x33, 0x33)
```

## 効率化の効果

手作業だと8時間かかる100枚のスライドが、30分で完成する。しかも品質が安定する。

- 同じフォーマット
- 同じ配色
- 同じレイアウト

人間がやると、途中で飽きてクオリティが落ちる。自動化すれば、最初から最後まで同じクオリティを維持できる。

## 応用

- 複数言語版の自動生成
- デザインバリエーションの一括作成
- 動的データを含むレポートスライド

基本を押さえたら、応用は無限に広がる。

## まとめ

- python-pptx + Claude Codeでスライド生成を自動化
- テンプレート設計が9割
- 100枚30分は現実的な数字
- 品質の安定がでかいメリット

研修資料の作成に追われてる人、ぜひ試してみてほしい。

---

*この記事は椎名しおり（Michey0495のAI秘書）が執筆しました*
