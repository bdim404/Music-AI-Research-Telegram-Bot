# Music AI News Bot

音乐 AI 新闻推送机器人，自动抓取 arXiv 音乐相关论文和 GitHub 热门项目，推送至 Telegram。

Automated bot that fetches music AI papers from arXiv and trending GitHub repos, sends to Telegram channel.

关注频道: [@MusicAIResearch](https://t.me/MusicAIResearch)

## Setup

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=@YourChannel
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1/
```

## Run

```bash
python -m src.main
```