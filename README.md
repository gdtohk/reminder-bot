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
