import warnings, json, psycopg2, uvicorn, time
from google import genai
from google.genai import types
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor

warnings.filterwarnings("ignore")
app = FastAPI()

# Enable CORS for frontend-backend communication
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db_connection():
    return psycopg2.connect(host="localhost", database="healflow", user="postgres", password="postgres")

# New token applied
client = genai.Client(api_key="AIzaSyAXCOUdXggojJDpflDB3WexEyZf6hxC1pk")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS signals;")
    cur.execute("""
        CREATE TABLE signals (
            id TEXT PRIMARY KEY, merchant TEXT, description TEXT, 
            status TEXT DEFAULT 'Pending', severity TEXT DEFAULT 'low',
            ai_data JSONB, feedback TEXT DEFAULT 'none'
        );
    """)
    issues = [
        ('ERR_001', 'Mumbai_Fashion', 'Checkout 404 error on legacy v1', 'low'),
        ('ERR_004', 'Delhi_Jewels', 'Exposed API keys in production logs', 'high'),
        ('ERR_006', 'Bangalore_Tech', 'Database deadlock in inventory', 'high')
    ]
    cur.executemany("INSERT INTO signals (id, merchant, description, severity) VALUES (%s,%s,%s,%s)", issues)
    conn.commit(); cur.close(); conn.close()

@app.get("/api/signals")
async def get_signals():
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM signals ORDER BY id ASC")
    res = cur.fetchall()
    cur.close(); conn.close()
    return res

@app.post("/api/signals/{signal_id}/heal")
async def heal(signal_id: str):
    time.sleep(1) # Artificial delay for demo visibility
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM signals WHERE id = %s", (signal_id,))
        signal = cur.fetchone()

        # RAG Logic: Finding past successful resolutions
        cur.execute("SELECT description, ai_data FROM signals WHERE status = 'Healed' AND feedback = 'positive' LIMIT 1")
        past = cur.fetchone()
        
        ctx = f"PAST SUCCESS: For '{past['description']}', we did '{past['ai_data']['orda_loop']['act']}'." if past else ""
        prompt = f"{ctx}\nIssue: {signal['description']}\nReturn JSON (analysis, orda_loop: observe, reason, decide, act)."
        
        resp = client.models.generate_content(
            model="gemini-3-flash-preview", 
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        ai_json = json.loads(resp.text)
        if past: ai_json['using_memory'] = True

        cur.execute("UPDATE signals SET ai_data = %s, status = 'Awaiting_Approval' WHERE id = %s", (json.dumps(ai_json), signal_id))
        conn.commit()
        return ai_json
    finally:
        cur.close(); conn.close()

@app.post("/api/signals/{signal_id}/accept")
async def accept(signal_id: str):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("UPDATE signals SET status = 'Healed' WHERE id = %s", (signal_id,))
    conn.commit(); cur.close(); conn.close()
    return {"status": "Healed"}

@app.post("/api/signals/{signal_id}/reject")
async def reject(signal_id: str):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("UPDATE signals SET status = 'Engineer_Assigned' WHERE id = %s", (signal_id,))
    conn.commit(); cur.close(); conn.close()
    return {"status": "Escalated"}

@app.post("/api/signals/add")
async def add(data: dict):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("INSERT INTO signals (id, merchant, description, severity) VALUES (%s,%s,%s,%s)", (data['id'], data['merchant'], data['description'], data['severity']))
    conn.commit(); cur.close(); conn.close()
    return {"status": "Added"}

@app.post("/api/signals/{signal_id}/feedback")
async def feedback(signal_id: str, data: dict):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("UPDATE signals SET feedback = %s WHERE id = %s", (data['vote'], signal_id))
    conn.commit(); cur.close(); conn.close()
    return {"status": "Logged"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)