#!/usr/bin/env python3
"""
Promotion Warrior - Database & Anti-Ban Tactical Engine
Companion script for SKILL.md (Universal Hunter Edition)

Provides:
- SQLite persistent storage for interaction histories and keyword rotations
- Automated URL sanitization (query param stripping and trailing slash normalization)
- 24-hour keyword rotation verification
- Strict URL deduplication to prevent duplicate replies and account bans
- Jaccard similarity check to enforce anti-clustering (>60% similarity rejection)
- Real-time quota and daily limit monitoring (Max 9 replies per day)
"""

import sys
import os
import re
import json
import sqlite3
from datetime import datetime

# Resolve database path dynamically relative to script location
DEFAULT_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'history.db'))
DB_PATH = os.environ.get('PROMOTION_WARRIOR_DB_PATH', DEFAULT_DB_PATH)

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            tier INTEGER NOT NULL,
            url TEXT NOT NULL UNIQUE,
            action TEXT NOT NULL,
            reply_snippet TEXT,
            target_user TEXT,
            niche TEXT DEFAULT 'default',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keyword_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            niche TEXT DEFAULT 'default',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def clean_url_str(url):
    if not url:
        return ""
    # Strip whitespace, query parameters, hash fragments, and trailing slashes
    cleaned = url.strip().split('?')[0].split('#')[0].rstrip('/')
    return cleaned

def stats():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as cnt FROM interactions WHERE date(timestamp) = date('now')")
    replies_today = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT COUNT(*) as cnt FROM interactions")
    total_interactions = cursor.fetchone()['cnt']
    
    max_limit = 9
    is_limit_reached = replies_today >= max_limit
    
    print(json.dumps({
        "replies_today": replies_today,
        "total_interactions": total_interactions,
        "max_daily_limit": max_limit,
        "is_limit_reached": is_limit_reached,
        "recommended_mode": "scout_only" if is_limit_reached else "scout_and_sniper"
    }, ensure_ascii=False))
    conn.close()

def check_keyword(keyword):
    kw = (keyword or "").strip().lower()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM keyword_logs WHERE LOWER(keyword) = ? AND timestamp >= datetime('now', '-24 hours')",
        (kw,)
    )
    cnt = cursor.fetchone()['cnt']
    used_last_24h = cnt > 0
    print(json.dumps({
        "used_last_24h": used_last_24h,
        "keyword": keyword
    }, ensure_ascii=False))
    conn.close()

def log_keyword(keyword, niche='default'):
    kw = (keyword or "").strip().lower()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO keyword_logs (keyword, niche) VALUES (?, ?)", (kw, niche))
    conn.commit()
    print(json.dumps({"logged": True, "keyword": keyword}, ensure_ascii=False))
    conn.close()

def check_url(url):
    cleaned = clean_url_str(url)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM interactions WHERE url = ?", (cleaned,))
    cnt = cursor.fetchone()['cnt']
    is_duplicate = cnt > 0
    print(json.dumps({
        "duplicate": is_duplicate,
        "url": cleaned
    }, ensure_ascii=False))
    conn.close()

def log_interaction(platform, tier, url, action, reply_snippet, target_user='', niche='default'):
    cleaned = clean_url_str(url)
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT INTO interactions 
               (platform, tier, url, action, reply_snippet, target_user, niche) 
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (platform, int(tier), cleaned, action, reply_snippet, target_user, niche)
        )
        conn.commit()
        print(json.dumps({
            "logged": True,
            "url": cleaned,
            "platform": platform,
            "tier": int(tier),
            "action": action
        }, ensure_ascii=False))
    except sqlite3.IntegrityError:
        print(json.dumps({
            "logged": False,
            "duplicate": True,
            "error": "IntegrityError (duplicate URL)"
        }, ensure_ascii=False))
    conn.close()

def tokenize(text):
    if not text:
        return set()
    # Match english words/numbers, and CJK characters/bigrams for accurate cross-language tokenization
    cjk_chars = re.findall(r'[\u4e00-\u9fff]', text)
    cjk_bigrams = [text[i:i+2] for i in range(len(text)-1) if re.match(r'[\u4e00-\u9fff]{2}', text[i:i+2])]
    words = set(re.findall(r'[a-zA-Z0-9]+', text.lower()))
    return words | set(cjk_bigrams) | set(cjk_chars)

def check_similarity(new_text, threshold=0.60):
    """
    Enforces Core Philosophy #2:
    '内容去重: 绝不发送两条相似度 >60% 的回复。'
    """
    new_tokens = tokenize(new_text)
    if not new_tokens or len(new_tokens) < 4:
        print(json.dumps({
            "allowed": True,
            "max_similarity": 0.0,
            "reason": "text too short to cluster"
        }, ensure_ascii=False))
        return

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT reply_snippet FROM interactions WHERE reply_snippet IS NOT NULL ORDER BY id DESC LIMIT 30"
    )
    rows = cursor.fetchall()
    conn.close()

    max_sim = 0.0
    conflicting_snippet = None

    for r in rows:
        prev_text = r['reply_snippet']
        prev_tokens = tokenize(prev_text)
        if not prev_tokens:
            continue
        intersection = len(new_tokens & prev_tokens)
        union = len(new_tokens | prev_tokens)
        sim = intersection / union if union > 0 else 0.0
        if sim > max_sim:
            max_sim = sim
            conflicting_snippet = prev_text

    is_allowed = max_sim < threshold
    result = {
        "allowed": is_allowed,
        "max_similarity": round(max_sim, 3),
        "threshold": threshold
    }
    if not is_allowed and conflicting_snippet:
        result["conflict_preview"] = conflicting_snippet[:80] + "..."
        result["directive"] = "Reject comment. Re-frame from a different angle to prevent platform clustering ban."
    print(json.dumps(result, ensure_ascii=False))

if __name__ == '__main__':
    init_db()
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == 'stats':
        stats()
    elif cmd == 'check_keyword' and len(sys.argv) >= 3:
        check_keyword(sys.argv[2])
    elif cmd == 'log_keyword' and len(sys.argv) >= 3:
        niche = sys.argv[3] if len(sys.argv) >= 4 else 'default'
        log_keyword(sys.argv[2], niche)
    elif cmd == 'check_url' and len(sys.argv) >= 3:
        check_url(sys.argv[2])
    elif cmd == 'log_interaction':
        # Handles standard: log_interaction "reddit" 1 "CLEAN_URL" "reply" "REPLY_SNIPPET" "TARGET_USERNAME"
        # Also handles optional niche as first or last argument
        if len(sys.argv) >= 7:
            platform = sys.argv[2]
            tier = sys.argv[3]
            url = sys.argv[4]
            action = sys.argv[5]
            reply_snippet = sys.argv[6]
            target_user = sys.argv[7] if len(sys.argv) >= 8 else ''
            niche = sys.argv[8] if len(sys.argv) >= 9 else 'default'
            log_interaction(platform, tier, url, action, reply_snippet, target_user, niche)
        else:
            print(json.dumps({"error": "Insufficient arguments for log_interaction"}))
            sys.exit(1)
    elif cmd == 'check_similarity' and len(sys.argv) >= 3:
        threshold = float(sys.argv[3]) if len(sys.argv) >= 4 else 0.60
        check_similarity(sys.argv[2], threshold)
    else:
        print(json.dumps({"error": f"Unknown command or invalid args: {cmd}"}))
        sys.exit(1)
