import sqlite3
import json
from contextlib import contextmanager
import os

# Create DB in backend directory
DB_FILE = os.path.join(os.path.dirname(__file__), "jobs.db")

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                status TEXT,
                processed INTEGER,
                total INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_results (
                job_id TEXT,
                row_index INTEGER,
                result TEXT,
                PRIMARY KEY (job_id, row_index)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS item_cache (
                item_hash TEXT PRIMARY KEY,
                result TEXT
            )
        ''')
        conn.commit()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE)
    try:
        yield conn
    finally:
        conn.close()

def create_job(job_id: str, total: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO jobs (id, status, processed, total) VALUES (?, ?, ?, ?)",
                       (job_id, "processing", 0, total))
        conn.commit()

def update_job_status(job_id: str, status: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        conn.commit()

def update_job_progress(job_id: str, processed: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE jobs SET processed = ? WHERE id = ?", (processed, job_id))
        conn.commit()

def save_row_result(job_id: str, row_index: int, result: dict):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO job_results (job_id, row_index, result) VALUES (?, ?, ?)",
                       (job_id, row_index, json.dumps(result)))
        conn.commit()

def get_job_results_dict(job_id: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT row_index, result FROM job_results WHERE job_id = ?", (job_id,))
        rows = cursor.fetchall()
        return {row[0]: json.loads(row[1]) for row in rows}

def get_job(job_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, processed, total FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if row:
            # fetch results
            cursor.execute("SELECT row_index, result FROM job_results WHERE job_id = ? ORDER BY row_index", (job_id,))
            res_rows = cursor.fetchall()
            results = [None] * row[2] # fill with None based on total
            for r_idx, r_val in res_rows:
                if r_idx < len(results):
                    results[r_idx] = json.loads(r_val)
                    
            # Filter out Nones for completed results
            results = [r for r in results if r is not None]
            
            return {
                "status": row[0],
                "processed": row[1],
                "total": row[2],
                "results": results
            }
        return None

def get_cached_item(item_hash: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT result FROM item_cache WHERE item_hash = ?", (item_hash,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None

def set_cached_item(item_hash: str, result: dict):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO item_cache (item_hash, result) VALUES (?, ?)",
                       (item_hash, json.dumps(result)))
        conn.commit()
