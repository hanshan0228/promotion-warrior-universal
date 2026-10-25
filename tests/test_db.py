#!/usr/bin/env python3
import os
import sys
import unittest
import json
import tempfile
import sqlite3

# Set temporary test database path
temp_dir = tempfile.mkdtemp()
test_db_path = os.path.join(temp_dir, 'test_history.db')
os.environ['PROMOTION_WARRIOR_DB_PATH'] = test_db_path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
import db

class TestPromotionWarriorDB(unittest.TestCase):
    def setUp(self):
        db.init_db()

    def tearDown(self):
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

    def test_clean_url_str(self):
        url = "https://reddit.com/r/marketing/comments/12345/best_tools/?utm_source=share&utm_medium=web2x&context=3#heading"
        expected = "https://reddit.com/r/marketing/comments/12345/best_tools"
        self.assertEqual(db.clean_url_str(url), expected)

    def test_log_and_check_keyword(self):
        # Initial check
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM keyword_logs WHERE keyword = 'test_kw'")
        self.assertEqual(cursor.fetchone()[0], 0)
        conn.close()

        # Log keyword
        db.log_keyword('test_kw')

        # Check keyword in db
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM keyword_logs WHERE keyword = 'test_kw'")
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()

    def test_url_deduplication(self):
        target_url = "https://reddit.com/r/tiktokads/comments/abc123/ad_issue/?ref=share"
        cleaned = db.clean_url_str(target_url)

        # Log interaction
        db.log_interaction("reddit", 1, target_url, "reply", "Try clearing cache and resetting pixel.", "user_alpha")

        # Check duplicate
        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM interactions WHERE url = ?", (cleaned,))
        self.assertEqual(cursor.fetchone()[0], 1)

        # Attempt to insert same URL again (should catch IntegrityError and not crash)
        db.log_interaction("reddit", 1, target_url, "reply", "Duplicate attempt", "user_beta")
        cursor.execute("SELECT COUNT(*) FROM interactions WHERE url = ?", (cleaned,))
        self.assertEqual(cursor.fetchone()[0], 1)
        conn.close()

    def test_jaccard_similarity(self):
        text1 = "Try resetting your pixel cookie in business manager to fix attribution issue"
        text2 = "Try resetting your pixel cookie in business manager to fix tracking issue"
        
        db.log_interaction("reddit", 1, "https://reddit.com/post/1", "reply", text1, "user1")
        
        tokens1 = db.tokenize(text1)
        tokens2 = db.tokenize(text2)
        sim = len(tokens1 & tokens2) / len(tokens1 | tokens2)
        self.assertGreater(sim, 0.60)

if __name__ == '__main__':
    unittest.main()
