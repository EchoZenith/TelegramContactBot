# Telegram Contact Bot (TG 客服机器人)

[![Docker](https://img.shields.io/badge/Docker-supported-blue.svg?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python)](https://www.python.org/)

这是一个基于 Python 开发的轻量级 Telegram 机器人，旨在为个人或小团队提供 **“私聊中转”** 服务。它可以作为你的私密客服通道，保护你的个人账号不被外界直接获知。

### 🌟 核心功能

- **双向转发**：用户发给机器人的消息会立即转发给你；你只需回复该转发消息，机器人便会代你回传。
- **无视隐私限制**：采用 SQLite 数据库记录消息映射关系，即使对方开启了“转发隐私保护”，你依然可以正常回复。
- **全媒体支持**：支持文字、图片、语音、视频、文件、贴纸等多种消息格式。
- **Docker 化部署**：支持 Docker Compose，一键运行，环境隔离，极致稳定。
- **欢迎语自定义**：自动处理 `/start` 命令，向首次访问的用户发送个性化引导。

---

### 🚀 快速开始

#### 1. 准备凭证
1.  **获取 Bot Token**: 在 Telegram 咨询 [@BotFather](https://t.me/BotFather) 创建机器人并获取 API Token。
2.  **获取 Admin ID**: 咨询 [@userinfobot](https://t.me/userinfobot) 获取你自己的 User ID（一串数字）。

#### 2. 下载与配置
克隆本仓库到你的服务器：
```bash
git clone https://github.com/EchoZenith/TelegramContactBot.git
cd TelegramContactBot/
```
复制示例配置文件并填入你的信息：
```bash
cp .env.example .env
nano .env
```
在 .env 中填入：
```bash
BOT_TOKEN=123456:ABC-DEFG...
ADMIN_ID=987654321
```

#### 3. 使用 Docker 部署 (推荐)
​只需一行命令：
```bash
docker-compose up -d --build
```

#### 🛠️ 手动部署 (非 Docker)
​如果你希望直接运行 Python 脚本：
##### 1. 安装依赖：
```bash
pip install -r requirements.txt
```
##### 2. 设置环境变量：
- ​Windows (PowerShell): $env:BOT_TOKEN="你的TOKEN"; $env:ADMIN_ID="你的ID"
- ​Linux/macOS: export BOT_TOKEN="你的TOKEN" ADMIN_ID="你的ID"
##### 3. 启动机器人：
```bash
python bot.py
```

### 📖 使用说明

1. ​**接收消息**：当有人给机器人发送消息时，你会收到一条由机器人转发的消息。
2. ​**回复消息**：在 Telegram 中**长按或右键点击**那条转发消息，选择 “**回复** (Reply)”，输入内容并发送。
3. **注意**：必须使用“**回复**”功能，否则机器人不知道该将消息回传给哪位用户。
### ​📂 项目结构

```
├── bot.py                # 核心逻辑代码
├── Dockerfile            # 容器构建文件
├── docker-compose.yml    # 编排定义
├── requirements.txt      # Python 依赖
├── .env.example          # 环境变量配置模板
└── data/                 # 数据库挂载目录 (运行后自动创建)
```
### ⚠️ 安全与隐私

- ​**Token 保护**：切勿将包含真实 Token 的 .env 文件提交到任何公共仓库。本仓库已默认忽略 .env。
- ​**数据持久化**：数据库存放在 ./data 目录下，建议定期备份 messages.db。

### ​🎁 鸣谢

​感谢以下项目及技术的支持：
- ​[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - 强大的 Telegram Bot 框架。
- ​[aiosqlite](https://github.com/omnilib/aiosqlite) - 优秀的异步 SQLite 库。
- ​[Docker](https://www.docker.com/) - 让部署变得如此简单。

### ​⚖️ 开源协议

​本项目基于 [MIT License](https://github.com/EchoZenith/TelegramContactBot/blob/main/LICENSE) 开源。