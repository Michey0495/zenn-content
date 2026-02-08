/**
 * note自動投稿スクリプト
 * Playwrightでnote.comにログインし、記事を投稿する
 */

import { chromium, Browser, Page } from 'playwright'
import * as fs from 'fs'
import * as path from 'path'
import * as dotenv from 'dotenv'

dotenv.config()

// 設定
const NOTE_EMAIL = process.env.NOTE_EMAIL
const NOTE_PASSWORD = process.env.NOTE_PASSWORD
const COOKIES_PATH = path.join(__dirname, '.note-cookies.json')

interface ArticleData {
  title: string
  body: string
  tags?: string[]
  thumbnailPath?: string
  publishNow?: boolean // falseなら下書き保存
}

// Cookieを保存
async function saveCookies(page: Page): Promise<void> {
  const cookies = await page.context().cookies()
  fs.writeFileSync(COOKIES_PATH, JSON.stringify(cookies, null, 2))
  console.log('Cookies saved')
}

// Cookieを読み込み
async function loadCookies(page: Page): Promise<boolean> {
  if (!fs.existsSync(COOKIES_PATH)) {
    return false
  }
  try {
    const cookies = JSON.parse(fs.readFileSync(COOKIES_PATH, 'utf-8'))
    await page.context().addCookies(cookies)
    console.log('Cookies loaded')
    return true
  } catch {
    return false
  }
}

// ログイン処理
async function login(page: Page): Promise<boolean> {
  if (!NOTE_EMAIL || !NOTE_PASSWORD) {
    console.error('NOTE_EMAIL and NOTE_PASSWORD must be set in .env')
    return false
  }

  console.log('Logging in to note.com...')

  // ログインページへ
  await page.goto('https://note.com/login')
  await page.waitForLoadState('networkidle')

  // メールアドレス入力
  await page.fill('input[name="login"]', NOTE_EMAIL)
  await page.fill('input[type="password"]', NOTE_PASSWORD)

  // ログインボタンをクリック
  await page.click('button[type="submit"]')

  // ログイン完了を待つ
  try {
    await page.waitForURL('**/dashboard**', { timeout: 30000 })
    console.log('Login successful')
    await saveCookies(page)
    return true
  } catch {
    // ダッシュボードにリダイレクトされない場合
    const currentUrl = page.url()
    if (currentUrl.includes('note.com') && !currentUrl.includes('login')) {
      console.log('Login successful (redirected to:', currentUrl, ')')
      await saveCookies(page)
      return true
    }
    console.error('Login failed')
    return false
  }
}

// ログイン状態を確認
async function checkLogin(page: Page): Promise<boolean> {
  await page.goto('https://note.com/dashboard')
  await page.waitForLoadState('networkidle')

  const url = page.url()
  return !url.includes('login')
}

// 記事を投稿
async function postArticle(page: Page, article: ArticleData): Promise<string | null> {
  console.log('Creating article:', article.title)

  // 新規投稿ページへ
  await page.goto('https://note.com/notes/new')
  await page.waitForLoadState('networkidle')

  // タイトル入力
  const titleInput = page.locator('textarea[placeholder*="タイトル"], input[placeholder*="タイトル"]')
  await titleInput.waitFor({ timeout: 10000 })
  await titleInput.fill(article.title)

  // 本文入力（noteのエディタはcontenteditable）
  const bodyEditor = page.locator('[contenteditable="true"]').first()
  await bodyEditor.waitFor({ timeout: 10000 })
  await bodyEditor.click()

  // Markdownを行ごとに入力
  const lines = article.body.split('\n')
  for (const line of lines) {
    await page.keyboard.type(line)
    await page.keyboard.press('Enter')
  }

  // 少し待機
  await page.waitForTimeout(2000)

  // サムネイル設定（オプション）
  if (article.thumbnailPath && fs.existsSync(article.thumbnailPath)) {
    console.log('Uploading thumbnail...')
    // サムネイル設定ボタンを探す
    const thumbnailButton = page.locator('button:has-text("見出し画像")')
    if (await thumbnailButton.isVisible()) {
      await thumbnailButton.click()
      const fileInput = page.locator('input[type="file"]')
      await fileInput.setInputFiles(article.thumbnailPath)
      await page.waitForTimeout(3000)
    }
  }

  // タグ設定（オプション）
  if (article.tags && article.tags.length > 0) {
    console.log('Adding tags:', article.tags)
    const tagInput = page.locator('input[placeholder*="タグ"]')
    if (await tagInput.isVisible()) {
      for (const tag of article.tags) {
        await tagInput.fill(tag)
        await page.keyboard.press('Enter')
        await page.waitForTimeout(500)
      }
    }
  }

  // 公開または下書き保存
  if (article.publishNow) {
    console.log('Publishing article...')
    // 公開ボタンを探す
    const publishButton = page.locator('button:has-text("公開")').first()
    await publishButton.click()

    // 公開確認ダイアログがある場合
    const confirmButton = page.locator('button:has-text("公開する")')
    if (await confirmButton.isVisible({ timeout: 3000 })) {
      await confirmButton.click()
    }

    // 公開完了を待つ
    await page.waitForTimeout(5000)
  } else {
    console.log('Saving as draft...')
    // 下書き保存
    const draftButton = page.locator('button:has-text("下書き保存")')
    if (await draftButton.isVisible()) {
      await draftButton.click()
      await page.waitForTimeout(3000)
    }
  }

  // 記事URLを取得
  const articleUrl = page.url()
  if (articleUrl.includes('/notes/') || articleUrl.includes('/n/')) {
    console.log('Article created:', articleUrl)
    return articleUrl
  }

  return null
}

// メイン処理
async function main(): Promise<void> {
  const args = process.argv.slice(2)

  if (args.length < 1) {
    console.log('Usage: npx ts-node scripts/note-post.ts <markdown-file> [--publish]')
    console.log('')
    console.log('Options:')
    console.log('  --publish    Publish immediately (default: save as draft)')
    console.log('')
    console.log('Example:')
    console.log('  npx ts-node scripts/note-post.ts articles/my-article.md')
    console.log('  npx ts-node scripts/note-post.ts articles/my-article.md --publish')
    process.exit(1)
  }

  const markdownPath = args[0]
  const publishNow = args.includes('--publish')

  if (!fs.existsSync(markdownPath)) {
    console.error('File not found:', markdownPath)
    process.exit(1)
  }

  // Markdownを読み込み
  const markdown = fs.readFileSync(markdownPath, 'utf-8')

  // フロントマターをパース
  const frontmatterMatch = markdown.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/)
  let title = ''
  let body = markdown
  let tags: string[] = []

  if (frontmatterMatch) {
    const frontmatter = frontmatterMatch[1]
    body = frontmatterMatch[2]

    // タイトル抽出
    const titleMatch = frontmatter.match(/title:\s*["']?(.+?)["']?\s*$/m)
    if (titleMatch) {
      title = titleMatch[1]
    }

    // タグ抽出
    const topicsMatch = frontmatter.match(/topics:\s*\[(.+?)\]/m)
    if (topicsMatch) {
      tags = topicsMatch[1].split(',').map(t => t.trim().replace(/["']/g, ''))
    }
  }

  // タイトルがない場合はファイル名から
  if (!title) {
    title = path.basename(markdownPath, '.md')
  }

  // note用にMarkdownを変換（Zenn独自記法を除去）
  body = body
    .replace(/:::(message|details|message alert)[\s\S]*?:::/g, '') // Zenn独自記法を除去
    .replace(/\n{3,}/g, '\n\n') // 3行以上の空行を2行に
    .trim()

  console.log('Title:', title)
  console.log('Tags:', tags)
  console.log('Publish:', publishNow ? 'Yes' : 'No (draft)')
  console.log('')

  // ブラウザ起動
  const browser: Browser = await chromium.launch({
    headless: false, // デバッグ用に表示
  })

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
  })

  const page = await context.newPage()

  try {
    // Cookie読み込み
    const hasCookies = await loadCookies(page)

    // ログイン確認
    let isLoggedIn = false
    if (hasCookies) {
      isLoggedIn = await checkLogin(page)
    }

    // 未ログインならログイン
    if (!isLoggedIn) {
      isLoggedIn = await login(page)
      if (!isLoggedIn) {
        console.error('Failed to login')
        process.exit(1)
      }
    }

    // 記事投稿
    const articleUrl = await postArticle(page, {
      title,
      body,
      tags,
      publishNow,
    })

    if (articleUrl) {
      console.log('')
      console.log('✅ Success!')
      console.log('URL:', articleUrl)
    } else {
      console.error('Failed to create article')
    }

  } catch (error) {
    console.error('Error:', error)
  } finally {
    // 少し待ってから閉じる
    await page.waitForTimeout(3000)
    await browser.close()
  }
}

main()
