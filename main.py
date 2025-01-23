import os
import hashlib
import sqlite3
from datetime import datetime
from telebot import TeleBot
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict

# إعداد المجلد الخاص بحفظ الملفات
UPLOAD_DIR = 'uploads'
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

class SecurityManager:
    @staticmethod
    def hash_data(data: str) -> str:
        """Generate a SHA256 hash for the input data."""
        return hashlib.sha256(data.encode()).hexdigest()

class DatabaseManager:
    def __init__(self, db_path: str = 'combo_bot.db'):
        self.db_path = db_path
        self.create_tables()

    def create_tables(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS combos (
                    id INTEGER PRIMARY KEY,
                    site TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    added_date DATETIME NOT NULL,
                    tags TEXT,
                    source TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS uploads (
                    id INTEGER PRIMARY KEY,
                    filename TEXT NOT NULL,
                    upload_date DATETIME NOT NULL
                )
            ''')
            conn.commit()

    def insert_combos_bulk(self, combos: List[Dict[str, str]]):
        """Insert multiple combos into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executemany('''
                INSERT INTO combos (site, username, password_hash, added_date, tags, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', combos)
            conn.commit()

    def insert_uploaded_file(self, filename: str):
        """Log uploaded file into the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO uploads (filename, upload_date)
                VALUES (?, ?)
            ''', (filename, datetime.now()))
            conn.commit()

class IntelligentComboBot:
    def __init__(self, bot_token: str):
        self.bot = TeleBot(bot_token)
        self.db = DatabaseManager()
        self.setup_commands()

    def setup_commands(self):
        """Define bot commands."""
        @self.bot.message_handler(commands=['start'])
        def start_command(message):
            self.bot.reply_to(message, """
🤖 Welcome to the Intelligent Combo Management Bot!

Commands:
- /add_combo: Add a new combo (format: site:username:password:tags)
- /upload_file: Upload a file containing combos
            """)

        @self.bot.message_handler(commands=['add_combo'])
        def add_combo_command(message):
            msg = self.bot.reply_to(message, "Enter combo details (format: site:username:password:tags)")
            self.bot.register_next_step_handler(msg, self.process_add_combo)

        @self.bot.message_handler(commands=['upload_file'])
        def upload_file_command(message):
            msg = self.bot.reply_to(message, "Please upload the text file containing combos.")
            self.bot.register_next_step_handler(msg, self.process_upload_file)

    def process_add_combo(self, message):
        try:
            parts = message.text.split(':')
            if len(parts) < 3:
                self.bot.reply_to(message, "Invalid format. Use site:username:password:tags")
                return

            site, username, password = parts[:3]
            tags = parts[3] if len(parts) > 3 else ''
            hashed_password = SecurityManager.hash_data(password)
            self.db.insert_combos_bulk([{
                'site': site,
                'username': username,
                'password_hash': hashed_password,
                'added_date': datetime.now(),
                'tags': tags,
                'source': 'manual'
            }])
            self.bot.reply_to(message, "Combo added successfully!")
        except Exception as e:
            self.bot.reply_to(message, f"Error: {str(e)}")

    def process_upload_file(self, message):
        try:
            if not message.document:
                self.bot.reply_to(message, "Error: No file uploaded.")
                return

            file_info = self.bot.get_file(message.document.file_id)
            downloaded_file = self.bot.download_file(file_info.file_path)

            # Save the file
            filename = os.path.join(UPLOAD_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(filename, 'wb') as f:
                f.write(downloaded_file)

            # Log the upload in the database
            self.db.insert_uploaded_file(filename)

            # Process the file
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            combos = []
            for line in lines:
                parts = line.strip().split(':')
                if len(parts) >= 3:
                    site, username, password = parts[:3]
                    tags = parts[3] if len(parts) > 3 else ''
                    combos.append((site, username, SecurityManager.hash_data(password), datetime.now(), tags, filename))

            self.db.insert_combos_bulk(combos)
            self.bot.reply_to(message, f"File processed successfully! {len(combos)} combos added.")
        except Exception as e:
            self.bot.reply_to(message, f"Error processing file: {str(e)}")

    def start(self):
        print("Intelligent Combo Bot is running...")
        self.bot.polling(none_stop=True)

# Bot Configuration
BOT_TOKEN = '7997069106:AAHe98Ii68ICmv0nnzn6h-r_I39vEibf2_4'
bot_instance = IntelligentComboBot(BOT_TOKEN)

if __name__ == "__main__":
    bot_instance.start()