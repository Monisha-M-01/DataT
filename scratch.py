import sqlite3, json
conn = sqlite3.connect('backend/jobs.db')
cur = conn.cursor()
cur.execute("SELECT results FROM jobs WHERE id='ff727aaa9c525298a784f4c6145a8b43'")
res = cur.fetchone()[0]
data = json.loads(res)
print(json.dumps([r.get('output', {}).get('_meta') or r.get('_meta') or r for r in data[:5]], indent=2))
