import sqlite3
import os
from datetime import datetime, timedelta
from modules.data_store import all_cards

# Use absolute path for DB to avoid "no such table" errors
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "lexi_wordbank.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Table for manual word bank (Notebook)
    c.execute('''CREATE TABLE IF NOT EXISTS words 
                 (word TEXT PRIMARY KEY, 
                  phonetic TEXT, 
                  definition_vi TEXT, 
                  definition_en TEXT,
                  word_class TEXT,
                  is_starred INTEGER DEFAULT 0,
                  date_added DATE DEFAULT CURRENT_DATE)''')
    
    # Table for topic-based cards (Lexi Cards)
    c.execute('''CREATE TABLE IF NOT EXISTS vocab 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  word TEXT UNIQUE, 
                  phonetic TEXT,
                  meaning TEXT, 
                  example TEXT, 
                  topic TEXT)''')

    # Table for Saved Reading Passages
    c.execute('''CREATE TABLE IF NOT EXISTS reading_history 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  topic TEXT,
                  content TEXT,
                  questions_json TEXT,
                  date_saved DATE DEFAULT CURRENT_DATE)''')
    
    # Simple migration: add new columns to words table if they don't exist
    for col in [("phonetic", "TEXT"), ("definition_vi", "TEXT"), ("definition_en", "TEXT"), ("word_class", "TEXT"), ("is_starred", "INTEGER DEFAULT 0")]:
        try:
            c.execute(f"ALTER TABLE words ADD COLUMN {col[0]} {col[1]}")
        except sqlite3.OperationalError:
            pass # Already exists
    
    # Migrate old data if necessary (one-time)
    try:
        c.execute("UPDATE words SET definition_vi = definition WHERE definition_vi IS NULL")
    except sqlite3.OperationalError:
        pass

    # Existing migration for vocab table
    try:
        c.execute("ALTER TABLE vocab ADD COLUMN phonetic TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def insert_all_cards():
    init_db()
    conn = get_connection()
    c = conn.cursor()
    for card in all_cards:
        try:
            c.execute("""
            INSERT OR IGNORE INTO vocab (word, phonetic, meaning, example, topic)
            VALUES (?, ?, ?, ?, ?)
            """, (card["word"], card.get("phonetic", ""), card["meaning"], card["example"], card["topic"]))
        except Exception as e:
            print(f"Error inserting {card['word']}: {e}")
    conn.commit()
    conn.close()

def save_word(word_data):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT OR REPLACE INTO words 
            (word, phonetic, definition_vi, definition_en, word_class) 
            VALUES (?, ?, ?, ?, ?)
        """, (
            word_data.get('word'),
            word_data.get('phonetic'),
            word_data.get('definition_vi'),
            word_data.get('definition_en'),
            word_data.get('word_class')
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"Save error: {e}")
        return False
    finally:
        conn.close()

def delete_word(word_to_delete):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM words WHERE word = ?", (word_to_delete,))
    conn.commit()
    conn.close()

def get_all_saved_words():
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT word, phonetic, definition_vi, definition_en, word_class, is_starred FROM words ORDER BY date_added DESC")
    rows = c.fetchall()
    conn.close()
    return [{
        "word": r[0],
        "phonetic": r[1],
        "definition_vi": r[2],
        "definition_en": r[3],
        "word_class": r[4],
        "is_starred": bool(r[5])
    } for r in rows]

def toggle_star(word, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE words SET is_starred = ? WHERE word = ?", (1 if status else 0, word))
    conn.commit()
    conn.close()

def get_cards_by_topic(topic):
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT word, phonetic, meaning, example FROM vocab WHERE topic = ?", (topic.lower(),))
    rows = c.fetchall()
    conn.close()
    return [{"word": r[0], "phonetic": r[1], "meaning": r[2], "example": r[3]} for r in rows]

def save_reading(data):
    import json
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO reading_history (title, topic, content, questions_json)
            VALUES (?, ?, ?, ?)
        """, (data['title'], data['topic'], data['content'], json.dumps(data['questions'])))
        conn.commit()
        return True
    except Exception as e:
        print(f"Reading save error: {e}")
        return False
    finally:
        conn.close()

def get_reading_history():
    import json
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, title, topic, content, questions_json, date_saved FROM reading_history ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return [{
        "id": r[0],
        "title": r[1],
        "topic": r[2],
        "content": r[3],
        "questions": json.loads(r[4]),
        "date_saved": r[5]
    } for r in rows]

def delete_reading(reading_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM reading_history WHERE id = ?", (reading_id,))
    conn.commit()
    conn.close()
