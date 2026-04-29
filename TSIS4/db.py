import psycopg2
from datetime import datetime

DB_PARAMS = {
    "dbname": "phonebook",
    "user": "postgres",
    "password": "1234567890",
    "host": "localhost"
}

def save_score(username, score, level):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # Insert or get player ID
        cur.execute("INSERT INTO players (username) VALUES (%s) ON CONFLICT (username) DO NOTHING", (username,))
        cur.execute("SELECT id FROM players WHERE username = %s", (username,))
        player_id = cur.fetchone()[0]
        
        # Insert session
        cur.execute("INSERT INTO game_sessions (player_id, score, level_reached) VALUES (%s, %s, %s)", 
                    (player_id, score, level))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

def get_leaderboard():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("""
            SELECT p.username, gs.score, gs.level_reached, gs.played_at 
            FROM game_sessions gs 
            JOIN players p ON gs.player_id = p.id 
            ORDER BY gs.score DESC LIMIT 10
        """)
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results
    except:
        return []

def get_personal_best(username):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("""
            SELECT MAX(gs.score) FROM game_sessions gs 
            JOIN players p ON gs.player_id = p.id 
            WHERE p.username = %s
        """, (username,))
        best = cur.fetchone()[0]
        cur.close()
        conn.close()
        return best if best else 0
    except:
        return 0
