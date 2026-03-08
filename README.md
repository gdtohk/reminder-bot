# 🤖 Telegram 全自動定時提醒機器人 (Serverless 旗艦版)

這是一個超輕量、零成本的 Telegram 專屬定時提醒機器人。純 Python 編寫，完美利用 Cloudflare Workers 與 D1 資料庫的免費額度運行，並透過 GitHub Actions 實現全自動部署！

## 🌟 核心特點
* **完全免費**：完美白嫖 Cloudflare 每日 10 萬次請求與免費 D1 資料庫。
* **Serverless 雲端大腦**：自帶 D1 SQL 資料庫記憶體，任務不怕遺失，永不當機。
* **精準時鐘**：透過 Cloudflare Cron Trigger 實現每分鐘自動檢查與推送提醒。
* **極簡部署**：Fork 本倉庫後，跟著下方步驟填入金鑰即可全自動上線，免除繁瑣的本地端環境設定。

---

## 🚀 部署教學 (保姆級 7 步指南)

### 第 1 步：準備基本金鑰
1. 在 Telegram 找 [@BotFather](https://t.me/BotFather) 申請一個機器人，獲取 **API Token**。
2. 在 Telegram 找 [@userinfobot](https://t.me/userinfobot) 獲取你的個人 **Chat ID**。
3. 登入 Cloudflare，在 API 權杖頁面建立一個具有 **編輯 Cloudflare Workers** 與 **編輯 D1 資料庫** 權限的 API Token，並記下你的 **Account ID (帳戶識別碼)**。

### 第 2 步：Fork 本倉庫
點擊右上角的 **Fork** 按鈕，將本專案複製到你自己的 GitHub 帳號下。

### 第 3 步：設定 GitHub 部署金鑰
在你 Fork 後的 GitHub 倉庫中：
1. 點擊 `Settings` -> `Secrets and variables` -> `Actions`。
2. 點擊 `New repository secret`，新增以下兩個環境變數：
   * `CF_ACCOUNT_ID` : 你的 Cloudflare 帳戶 ID
   * `CF_API_TOKEN` : 你的 Cloudflare API 密碼

### 第 4 步：建立 Cloudflare D1 資料庫 (大腦記憶體)
1. 登入 Cloudflare 後台，進入左側選單的 **「儲存和資料庫 (Storage & Databases)」** -> **「D1 SQL 資料庫」**。
2. 點擊「建立」，名稱請填寫：`reminder_db`。
3. 建立完成後，**複製畫面上的「資料庫 ID (Database ID)」** 備用。
4. 點擊進入剛建好的 `reminder_db`，切換到 **「控制台 (Console)」** 標籤。
5. 貼上以下 SQL 語法並點擊「執行」，建立記憶表格：
```sql
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    message TEXT NOT NULL,
    remind_time DATETIME NOT NULL,
    is_sent INTEGER DEFAULT 0
);
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    message TEXT NOT NULL,
    remind_time DATETIME NOT NULL,
    is_sent INTEGER DEFAULT 0
);
```  <-- ❗️ 就是要在這裡補上這三個反引號 ( ``` )
### 第 5 步：綁定資料庫與啟動部署
1. 回到你的 GitHub 倉庫，打開 `wrangler.toml` 檔案，點擊編輯。
2. 將最下方的 `database_id = "..."` 替換成你在第 4 步複製的 **資料庫 ID**。
3. 儲存 (Commit changes) 後，前往 GitHub 的 **Actions** 標籤頁，確認自動部署任務 (Deploy) 出現綠色的 ✅ 成功標誌。

### 第 6 步：設定 Telegram 通訊金鑰
部署成功後，回到 Cloudflare 後台：
1. 進入 **Workers & Pages**，找到剛部署好的 `reminder-bot`。
2. 進入 **設定 (Settings)** -> **變數與機密 (Variables and Secrets)**。
3. 點擊新增變數（**類型務必選擇「機密 / Secret」**），新增以下兩個：
   * 變數名稱 `TELEGRAM_TOKEN` : 值填入你的 Telegram 機器人 Token
   * 變數名稱 `TELEGRAM_CHAT_ID` : 值填入你的個人 Chat ID
4. 點擊「儲存」或「部署」讓金鑰生效。

### 第 7 步：打通耳朵 (綁定 Webhook)
打開瀏覽器，訪問你專屬的 Worker 網址並加上 `/setup` 尾綴：
👉 `https://你的機器人網址.workers.dev/setup`
*(只要網頁顯示包含 `"Webhook was set"` 的成功訊息，機器人就正式活過來啦！)*

---

## 💬 機器人使用說明

打開你的 Telegram 機器人，直接發送以下指令來新增提醒：

**👉 新增任務格式：**
請使用 24 小時制的香港時間：`/add YYYY-MM-DD HH:MM 你的任務內容`

**📝 實際範例：**
* `/add 2026-03-08 15:30 記得提交鋼筋圖紙`
* `/add 2026-03-09 09:00 提醒 QS 開會`

只要發送成功，機器人會回覆「✅ 任務已記錄入庫！」。接著你什麼都不用管，只要時間一到，機器人就會透過 Cloudflare 的定時器全自動發送提醒給你！

