# Music AI News Bot

音乐 AI 新闻推送机器人，自动抓取 arXiv 论文（cs.SD, cs.MM, eess.AS）和 GitHub 热门项目，智能过滤音乐 AI 相关内容并推送至 Telegram。

涵盖领域：音乐生成、音频合成、音源分离、音乐转录、节拍跟踪、和弦识别、旋律提取、歌声合成、音频分类、音乐推荐、MIR、频谱分析、MIDI、音高检测、音色、声学模型、流派分类、情绪检测、歌词、混音、母带、乐谱等。

Automated bot that fetches music AI papers from arXiv (cs.SD, cs.MM, eess.AS) and trending GitHub repos, filters by music AI keywords, sends to Telegram channel.

Covers: music generation, audio synthesis, source separation, music transcription, beat tracking, chord recognition, melody extraction, singing voice, audio classification, music recommendation, MIR, spectrogram, MIDI, pitch detection, timbre, acoustic models, genre classification, mood detection, lyrics, mixing, mastering, music score, etc.

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
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

## Deploy with systemd

Edit `music-ai-news-bot.service` and `music-ai-news-bot.timer`, replace `/path/to/AI-News-Aggregator-Bot` and `your_username`, then:

```bash
sudo cp music-ai-news-bot.service /etc/systemd/system/
sudo cp music-ai-news-bot.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable music-ai-news-bot.timer
sudo systemctl start music-ai-news-bot.timer
```