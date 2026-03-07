# 🤖 Telegram 定时提醒机器人 (基于 Cloudflare Workers)

这是一个超轻量、零成本的 Telegram 提醒机器人后端代码。纯 Python 编写，利用 Cloudflare Workers 免费额度运行，并通过 GitHub Actions 实现全自动部署！

## 🌟 特点
- **零成本**：完美白嫖 Cloudflare 每日 10 万次免费请求。
- **免运维**：无需购买 VPS，Serverless 架构，永不宕机。
- **极简部署**：Fork 本仓库后，填入你的金钥即可自动上线。

---

## 🚀 部署教程 (只需 4 步)

### 1. 准备工作
- 找 [@BotFather](https://t.me/BotFather) 申请一个 Telegram Bot，获取 `API Token`。
- 找 [@userinfobot](https://t.me/userinfobot) 获取你的个人 `Chat ID`。
- 获取你的 Cloudflare `Account ID` 和 `API Token` (需要 Edit Cloudflare Workers 权限)。

### 2. Fork 本仓库
点击右上角的 **Fork** 按钮，将本项目复制到你的 GitHub 账号下。

### 3. 配置 GitHub Secrets (触发自动部署)
在**你 Fork 后的仓库**中，点击 `Settings` -> `Secrets and variables` -> `Actions`，点击 `New repository secret` 添加以下两个机密变量：
- `CF_ACCOUNT_ID` : 你的 Cloudflare 账户 ID
- `CF_API_TOKEN` : 你的 Cloudflare API 密钥

> 💡 添加完成后，前往 `Actions` 标签页，手动同意启用 Workflows，修改任意代码或手动触发一次 Push，GitHub 就会自动帮你部署到 Cloudflare！

### 4. 在 Cloudflare 填写 Telegram 变量
部署成功后，登录 Cloudflare 后台：
1. 进入 `Workers & Pages`，找到刚部署好的 `reminder-bot`。
2. 进入 `Settings` (设置) -> `Variables and Secrets` (变量与机密)。
3. 添加以下两个**加密变量 (Encrypt)**：
   - `TELEGRAM_TOKEN` : 填入你的 Telegram 机器人 Token
   - `TELEGRAM_CHAT_ID` : 填入你的 Telegram Chat ID
4. 保存后即可生效！现在你可以访问你的 Worker 域名，测试机器人是否成功给你发消息啦！