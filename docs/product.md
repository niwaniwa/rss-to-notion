# Notion RSS 購読システム 要件定義

## 目的
- 指定した RSS/Atom フィードを定期取得し、重複なく Notion データベースに追記・更新する
- 運用は GitHub Actions のスケジュール実行で全自動化（手動トリガも可）
  - RSS のrepositoryはPullReqで運用する

---

## 入出力

### 入力
- RSS/Atom URL の配列（`feeds.json` 等）
- 環境変数（Notion 統合トークン、データベース ID）

### 出力（Notion DB のレコード）
- **Title**（記事タイトル, title）
- **URL**（url）
- **PublishedAt**（日時, date）
- **Source**（フィード名/ドメイン, select）
- **GUID**（内部キー, text）
- **Summary**（リード文, text）
- **Tags**（RSS `<category>` から, multi-select）

tagは表記ゆれがあるため新たな列にAItagを追加することを検討
---

## 同期仕様
- **重複判定**：`GUID`（なければ `link+published` のハッシュ）
- **Upsert**：既存 `GUID` があれば更新、なければ作成
- **正規化**：本文 HTML → テキスト要約（例：先頭500字）
- **タイムゾーン**：保存は UTC、表示は Notion 側で JST

---

## スケジュール・運用
- GitHub Actions `on.schedule` で最短 **5分間隔**
  - 基本的に一日一回実行
- 混雑回避のため 00/30 分以外に設定（例：`7,37 * * * *`）
- 手動再実行：`workflow_dispatch`
- ログ&結果：差分件数を出力、必要なら Artifacts に保存

---

## レート制御・再試行
- **Notion API 制限**：平均 **3 req/s**、429 受信時は `Retry-After` 準拠
- **ページネーション**：`page_size<=100` ＋ `next_cursor` でループ

---

## GitHub Actions 設計
- ランナー：`ubuntu-latest`
- 権限：`permissions: contents: read`
- シークレット：`NOTION_TOKEN`, `NOTION_DATABASE_ID`
- **併走制御**：`concurrency` で同一ブランチは 1 本に制御
- タイムアウト：1 ジョブ最大 **6時間**
  - ただしここでは15分に設定する

---

## 失敗時ハンドリング
- 429/5xx：再試行
- RSS 取得失敗：当該フィードのみスキップ
- 全体失敗時：通知ステップに移行

---

## セキュリティ
- Secrets は GitHub Secrets で管理

---
