# RSS to Notion

RSSフィードから記事を自動取得してNotionデータベースに同期するシステム

## 機能

- 複数RSSフィードの一括処理
- Notionデータベースへの自動同期（Upsert）
- 重複記事の検出・更新
- GitHub Actionsによる自動実行
- レート制限対応

## セットアップ

### 1. Notion設定

1. Notion Integration を作成
   - https://www.notion.so/my-integrations でIntegrationを作成
   - Integration Tokenをコピー

2. Notionデータベースを作成・設定
   - 以下のプロパティを持つデータベースを作成:
     - Title (タイトル)
     - URL (URL)  
     - PublishedAt (日付)
     - Source (セレクト)
     - GUID (テキスト)
     - Summary (テキスト)
     - Tags (マルチセレクト)
   - データベースをIntegrationと共有

### 2. 環境設定

```bash
# 依存関係インストール
pip install -r requirements.txt

# 環境変数設定
cp .env.example .env
# .envファイルを編集してTokenとDatabase IDを設定
```

### 3. feeds.json設定

```json
{
  "feeds": [
    {
      "url": "https://example.com/rss.xml",
      "name": "Example Blog", 
      "tags": ["tech", "blog"]
    }
  ]
}
```

## 使用方法

### ローカル実行
```bash
python ./src/main.py
```

### GitHub Actions設定

1. リポジトリのSecretsに以下を設定:
   - `NOTION_TOKEN`: Notion Integration Token
   - `NOTION_DATABASE_ID`: NotionデータベースID

2. 毎日自動実行
3. 手動実行も可能（Actionsタブから）

## 出力フィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| Title | タイトル | 記事タイトル |
| URL | URL | 記事URL |
| PublishedAt | 日付 | 公開日時 |
| Source | セレクト | フィード名 |
| GUID | テキスト | 内部キー（重複判定用） |
| Summary | テキスト | 記事概要（500文字） |
| Tags | マルチセレクト | タグ（RSSカテゴリ + フィード設定） |