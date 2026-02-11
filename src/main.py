import asyncio
import os
import time
import logging
from telegram import Bot
from telegram.error import RetryAfter, TimedOut
from telegram.constants import ParseMode
import html
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

from src.utils import (
    get_rss_feed_items,
    get_github_trending_repos,
    get_source_emoji,
    extract_arxiv_id,
    get_research_blog_items
)
from src.db import load_sent_links, save_sent_link, initialize_db
from src.translator import generate_summary

# --- Configuration Variables ---
# Bot token and channel ID will be read from GitHub Secrets or environment variables.
# For local testing, you can set them here directly or use a .env file.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TELEGRAM_CHANNEL_ID_FOR_FOOTER = TELEGRAM_CHANNEL_ID

bot = None

def get_bot():
    global bot
    if bot is None:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
    return bot # No longer "Hardcoded" as a literal string

# --- Function Definitions ---

def format_telegram_post(title, link, summary, source_name_for_emoji_lookup, one_line_summary=None, published_time=None, sent_time=None, tags=None):
    from datetime import datetime
    escaped_title = html.escape(title)
    escaped_summary = html.escape(summary) if summary else ""

    time_info = ""
    if published_time:
        time_info += f"发布时间: {published_time}\n"
    if sent_time:
        time_info += f"推送时间: {sent_time}\n"

    if "arxiv" in source_name_for_emoji_lookup.lower():
        arxiv_id = extract_arxiv_id(link)

        post_content = (
            f"<b>{escaped_title}</b>\n\n"
            f"<b>摘要：</b>{escaped_summary}\n\n"
        )

        if time_info:
            post_content += f"{time_info}\n"

        post_content += f"<a href='{link}'>论文链接</a>"

        if arxiv_id:
            pdf_link = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            post_content += f" | <a href='{pdf_link}'>PDF</a>"

        if one_line_summary:
            post_content += f"\n\n{one_line_summary}"

        if tags and len(tags) > 0:
            tags_text = " ".join([f"#{tag}" for tag in tags])
            post_content += f"\n\n{tags_text}"
    else:
        if not escaped_summary or escaped_summary.strip().lower() in [
            "no description available.",
            "click to read more or join the discussion."
        ]:
            summary_text = ""
        else:
            summary_text = f"\n\n{escaped_summary}"

        post_content = (
            f"<b>{escaped_title}</b>"
            f"{summary_text}"
        )

        if time_info:
            post_content += f"\n\n{time_info}"

        post_content += f"\n<a href='{link}'>Read More</a>"

    return post_content


async def collect_and_send_news(sent_links):
    logger.info("\n[MAIN] Starting news collection and sending")
    logger.info(f"[MAIN] Database has {len(sent_links)} links")

    total_sent = 0

    logger.info("[SOURCE] arXiv cs.SD")
    items = get_rss_feed_items(
        "https://rss.arxiv.org/rss/cs.SD",
        "arXiv cs.SD",
        sent_links,
        limit=5,
        translate=True,
        filter_music=False
    )
    total_sent += await send_news_to_telegram(items, sent_links)

    logger.info("[SOURCE] arXiv cs.MM")
    items = get_rss_feed_items(
        "https://rss.arxiv.org/rss/cs.MM",
        "arXiv cs.MM",
        sent_links,
        limit=5,
        translate=True,
        filter_music=True
    )
    total_sent += await send_news_to_telegram(items, sent_links)

    logger.info("[SOURCE] arXiv eess.AS")
    items = get_rss_feed_items(
        "https://rss.arxiv.org/rss/eess.AS",
        "arXiv eess.AS",
        sent_links,
        limit=5,
        translate=True,
        filter_music=False
    )
    total_sent += await send_news_to_telegram(items, sent_links)

    logger.info("[SOURCE] GitHub Trending (Python)")
    items = get_github_trending_repos(
        language="python",
        sent_links=sent_links,
        limit=3,
        filter_music=True
    )
    total_sent += await send_news_to_telegram(items, sent_links)

    logger.info("[SOURCE] GitHub Trending (Jupyter)")
    items = get_github_trending_repos(
        language="jupyter-notebook",
        sent_links=sent_links,
        limit=3,
        filter_music=True
    )
    total_sent += await send_news_to_telegram(items, sent_links)

    logger.info(f"[MAIN] Finished. Total sent: {total_sent}")
    return total_sent


async def send_news_to_telegram(news_items, sent_links):
    from datetime import datetime
    if not news_items:
        return 0

    sent_count = 0

    for title, link, summary, source_name_for_emoji_lookup, one_line_summary, published_time, tags in news_items:
        if link in sent_links:
            continue

        sent_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = format_telegram_post(title, link, summary, source_name_for_emoji_lookup, one_line_summary, published_time, sent_time, tags)

        try:
            logger.info(f"[SEND] {title[:60]}")
            await get_bot().send_message(chat_id=TELEGRAM_CHANNEL_ID, text=formatted_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            save_sent_link(link, published_time)
            sent_links.add(link)
            sent_count += 1
            await asyncio.sleep(3)
        except RetryAfter as e:
            wait_time = e.retry_after + 1
            logger.warning(f"[SEND] Flood control, waiting {wait_time}s")
            await asyncio.sleep(wait_time)

            try:
                await get_bot().send_message(chat_id=TELEGRAM_CHANNEL_ID, text=formatted_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                save_sent_link(link, published_time)
                sent_links.add(link)
                sent_count += 1
                await asyncio.sleep(3)
            except Exception as retry_e:
                logger.error(f"[SEND] Retry failed: {retry_e}", exc_info=True)

        except TimedOut:
            logger.warning(f"[SEND] Timeout, retrying in 5s")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"[SEND] Failed: {e}", exc_info=True)

    return sent_count


async def check_bot_permissions(bot):
    try:
        chat = await bot.get_chat(chat_id=TELEGRAM_CHANNEL_ID)
        logger.info(f"[CHANNEL] Title: {chat.title}")
        logger.info(f"[CHANNEL] Type: {chat.type}")
        logger.info(f"[CHANNEL] Username: @{chat.username if chat.username else 'N/A'}")

        me = await bot.get_me()
        bot_member = await bot.get_chat_member(chat_id=TELEGRAM_CHANNEL_ID, user_id=me.id)
        logger.info(f"[CHANNEL] Bot status: {bot_member.status}")
        if hasattr(bot_member, 'can_post_messages'):
            logger.info(f"[CHANNEL] Can post: {bot_member.can_post_messages}")
        return True
    except Exception as e:
        logger.error(f"[CHANNEL] Check failed: {e}", exc_info=True)
        return False

async def main_bot_run():
    start_time = time.time()

    logger.info(f"\n[MAIN] Started at {time.ctime()}")
    logger.info(f"[MAIN] Bot: {TELEGRAM_BOT_TOKEN[:20]}...")
    logger.info(f"[MAIN] Channel: {TELEGRAM_CHANNEL_ID}")

    bot = get_bot()
    async with bot:
        if not await check_bot_permissions(bot):
            logger.error("[MAIN] Permission check failed")
            return

        initialize_db()
        sent_links = load_sent_links()

        await collect_and_send_news(sent_links)

    duration = time.time() - start_time
    logger.info(f"[MAIN] Finished at {time.ctime()}")
    logger.info(f"[MAIN] Duration: {duration:.1f}s")

# This block ensures main_bot_run() is executed when the script is run directly.
if __name__ == "__main__":
    asyncio.run(main_bot_run())
