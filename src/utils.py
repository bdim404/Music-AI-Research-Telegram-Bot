import feedparser
import requests
from bs4 import BeautifulSoup
import time
import re
import logging

from src.translator import translate_paper_all_in_one
from src.filters import is_music_ai_related

logger = logging.getLogger(__name__)

def get_source_emoji(source_name):
    return ""

# --- Define a common User-Agent header ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Connection': 'keep-alive',
}


def get_rss_feed_items(feed_url, source_name, sent_links, limit=15, translate=True, filter_music=True):
    logger.info(f"[RSS_FETCH] Retrieving news from RSS: {source_name} ({feed_url})")
    items = []
    try:
        feed = feedparser.parse(feed_url)
        logger.info(f"[RSS_FETCH] Found {len(feed.entries)} entries in feed")
        for entry in feed.entries[:limit]:
            title = getattr(entry, 'title', "No Title")
            link = getattr(entry, 'link', None)

            if not link:
                logger.info(f"[RSS_SKIP] No link found for entry: {title[:50]}")
                continue
            if link in sent_links:
                logger.info(f"[RSS_SKIP] Already sent: {title[:50]}")
                continue

            published_time = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                from time import strftime
                published_time = strftime("%Y-%m-%d %H:%M:%S", entry.published_parsed)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                from time import strftime
                published_time = strftime("%Y-%m-%d %H:%M:%S", entry.updated_parsed)

            summary = getattr(entry, 'summary', getattr(entry, 'description', title))
            summary = BeautifulSoup(summary, "html.parser").get_text(separator=' ', strip=True)

            if "arxiv" in feed_url.lower():
                summary = re.sub(r'arXiv:\d+\.\d+v\d+\s+Announce Type:\s+\w+\s*', '', summary)
                summary = re.sub(r'Abstract:\s*', '', summary)
                summary = summary.strip()

            if filter_music and not is_music_ai_related(title, summary):
                logger.info(f"[RSS_FILTER] Not music/AI related: {title[:50]}")
                continue

            one_line_summary = None
            tags = []
            if "arxiv" in feed_url.lower() and translate and summary:
                logger.info(f"[RSS_TRANSLATE] Translating: {title[:50]}...")
                result = translate_paper_all_in_one(title, summary)
                title = result["title"]
                summary = result["abstract"]
                one_line_summary = result["summary"]
                tags = result.get("tags", [])

            summary = (summary[:500] + '...') if len(summary) > 500 else summary

            time.sleep(0.3)
            items.append((title, link, summary, source_name, one_line_summary, published_time, tags))
            logger.info(f"[RSS_ADD] Added: {title[:50]} (Published: {published_time})")

        logger.info(f"[RSS_FETCH] Collected {len(items)} items from {source_name}")
        return items
    except Exception as e:
        logger.error(f"[RSS_ERROR] Error retrieving RSS from {source_name}: {e}", exc_info=True)
        
        
        return []

def extract_arxiv_id(url):
    match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', url)
    return match.group(1) if match else None

def get_research_blog_items(blog_url, source_name, sent_links, limit=10):
    logger.info(f"Retrieving news from Research Blog: {source_name} ({blog_url})")
    items = []
    try:
        time.sleep(1)
        res = requests.get(blog_url, headers=HEADERS)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        if "magenta" in blog_url.lower():
            articles = soup.select("article.post, div.post-preview, .blog-post")[:limit]
            for article in articles:
                title_tag = article.select_one("h2 a, h3 a, .post-title a, a.post-link")
                desc_tag = article.select_one("p, .post-excerpt, .excerpt")

                if title_tag:
                    title = title_tag.text.strip()
                    link = title_tag.get("href", "")
                    if link and not link.startswith("http"):
                        link = "https://magenta.withgoogle.com" + link

                    summary = desc_tag.text.strip() if desc_tag else "No description available."
                    summary = (summary[:300] + '...') if len(summary) > 300 else summary

                    if link and link not in sent_links and is_music_ai_related(title, summary):
                        items.append((f"{source_name}: {title}", link, summary, source_name, None))

        elif "spotify" in blog_url.lower():
            articles = soup.select("article, .post-item, .research-item")[:limit]
            for article in articles:
                title_tag = article.select_one("h2 a, h3 a, .title a")
                desc_tag = article.select_one("p, .excerpt, .description")

                if title_tag:
                    title = title_tag.text.strip()
                    link = title_tag.get("href", "")
                    if link and not link.startswith("http"):
                        link = "https://research.atspotify.com" + link

                    summary = desc_tag.text.strip() if desc_tag else "No description available."
                    summary = (summary[:300] + '...') if len(summary) > 300 else summary

                    if link and link not in sent_links and is_music_ai_related(title, summary):
                        items.append((f"{source_name}: {title}", link, summary, source_name, None))

        elif "adobe" in blog_url.lower():
            articles = soup.select("article, .research-item, .publication")[:limit]
            for article in articles:
                title_tag = article.select_one("h2 a, h3 a, .title a")
                desc_tag = article.select_one("p, .abstract, .description")

                if title_tag:
                    title = title_tag.text.strip()
                    link = title_tag.get("href", "")
                    if link and not link.startswith("http"):
                        link = "https://research.adobe.com" + link

                    summary = desc_tag.text.strip() if desc_tag else "No description available."
                    summary = (summary[:300] + '...') if len(summary) > 300 else summary

                    if link and link not in sent_links and is_music_ai_related(title, summary):
                        items.append((f"{source_name}: {title}", link, summary, source_name, None))

        return items
    except Exception as e:
        logger.info(f"Error retrieving research blog from {source_name}: {e}")
        return []

def get_hacker_news_items(sent_links, limit=10):
    """
    Retrieves top news items from Hacker News API, including title, link, and a short summary.
    No emoji prefix is added here, as it's handled by format_telegram_post.

    Args:
        sent_links (set): A set of previously sent links to avoid duplicates.
        limit (int): Maximum number of items to return.

    Returns:
        list: A list of tuples (title, link, summary, source_name_for_emoji_lookup).
    """
    source_name = "Hacker News"
    logger.info(f"Retrieving news from Hacker News")
    items = []
    try:
        top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"

        # --- Delay before first request to Hacker News ---
        time.sleep(1)
        
        top_story_ids = requests.get(top_stories_url).json()

        for story_id in top_story_ids[:limit]:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"

            # --- Delay before each individual story request ---
            time.sleep(0.5)
            
            story_data = requests.get(item_url).json()

            title = story_data.get('title', "No Title")
            link = story_data.get('url', f"https://news.ycombinator.com/item?id={story_id}")
            summary = story_data.get('text', "Click to read more or join the discussion.")
            summary = BeautifulSoup(summary, "html.parser").get_text(separator=' ', strip=True)
            summary = (summary[:200] + '...') if len(summary) > 200 else summary

            if title and link and link not in sent_links:
                items.append((f"{source_name}: {title}", link, summary, source_name))
            else:
                if link:
                    logger.info(f"Duplicate link from {source_name} ignored: {link}")
        return items
    except requests.exceptions.RequestException as e:
        logger.info(f"Error retrieving Hacker News: {e}")
        return []
    except Exception as e:
        logger.info(f"General error in Hacker News: {e}")
        return []

def get_github_trending_repos(language, sent_links, limit=10, filter_music=True):
    from datetime import datetime
    source_name = f"GitHub Trending ({language})"
    url = f"https://github.com/trending/{language}"
    logger.info(f"[GITHUB_FETCH] Retrieving news from GitHub Trending: {language} ({url})")
    items = []
    try:
        time.sleep(1)

        res = requests.get(url, headers=HEADERS)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")

        trending_date = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"[GITHUB_FETCH] Found {len(soup.select('article.Box-row'))} trending repos")

        for article_tag in soup.select("article.Box-row")[:limit * 2]:
            title_tag = article_tag.select_one("h2 a")
            description_tag = article_tag.select_one("p.col-9")

            repo_name = title_tag.text.strip().replace("\n", "").replace(" ", "") if title_tag else "No Repository Name"
            link = "https://github.com" + title_tag["href"] if title_tag and "href" in title_tag.attrs else None
            summary = description_tag.text.strip() if description_tag else "No description available."

            if not link:
                continue
            if link in sent_links:
                logger.info(f"[GITHUB_SKIP] Already sent: {repo_name}")
                continue

            if filter_music and language not in ["music", "audio", "music-generation"]:
                if not is_music_ai_related(repo_name, summary):
                    logger.info(f"[GITHUB_FILTER] Not music/AI related: {repo_name}")
                    continue

            summary = (summary[:300] + '...') if len(summary) > 300 else summary

            items.append((f"{source_name}: {repo_name}", link, summary, source_name, None, trending_date, []))
            logger.info(f"[GITHUB_ADD] Added: {repo_name}")
            if len(items) >= limit:
                break

        logger.info(f"[GITHUB_FETCH] Collected {len(items)} items from GitHub Trending")
        return items
    except requests.exceptions.RequestException as e:
        logger.error(f"[GITHUB_ERROR] Error retrieving GitHub Trending: {e}", exc_info=True)
        
        
        return []
    except Exception as e:
        logger.error(f"[GITHUB_ERROR] General error in GitHub Trending: {e}", exc_info=True)
        
        
        return []
