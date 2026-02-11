import sqlite3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_FILE = os.path.join(os.getenv("GITHUB_WORKSPACE", "."), "sent_links.db")

def initialize_db():
    db_dir = os.path.dirname(DB_FILE)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
        logger.info(f"[DB_INIT] Created directory for DB: {db_dir}")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sent (
            link TEXT PRIMARY KEY,
            published_time TEXT,
            sent_time TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    logger.info(f"[DB_INIT] Database '{DB_FILE}' initialized successfully")
    logger.info(f"[DB_INIT] Database location: {os.path.abspath(DB_FILE)}")

def load_sent_links():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT link FROM sent")
    links = {row[0] for row in cursor.fetchall()}
    conn.close()
    logger.info(f"[DB_LOAD] Loaded {len(links)} previously sent links from DB")
    if len(links) > 0:
        cursor = sqlite3.connect(DB_FILE).cursor()
        cursor.execute("SELECT link, published_time, sent_time FROM sent ORDER BY sent_time DESC LIMIT 3")
        recent = cursor.fetchall()
        logger.info(f"[DB_LOAD] Recent entries:")
        for link, pub_time, sent_time in recent:
            logger.info(f"[DB_LOAD]   - {link[:50]}... (Published: {pub_time}, Sent: {sent_time})")
    return links

def save_sent_link(link, published_time=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    sent_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            "INSERT INTO sent (link, published_time, sent_time) VALUES (?, ?, ?)",
            (link, published_time, sent_time)
        )
        conn.commit()
        logger.info(f"[DB_SAVE] Saved link: {link[:50]}... (Published: {published_time}, Sent: {sent_time})")
    except sqlite3.IntegrityError:
        logger.info(f"[DB_SAVE] Link already exists in DB: {link[:50]}...")
    finally:
        conn.close()
