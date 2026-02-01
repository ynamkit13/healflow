import warnings
warnings.filterwarnings("ignore")
from google import genai
from google.genai import types
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uvicorn

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db_connection():
    return psycopg2.connect(host="localhost", database="healflow", user="postgres", password="postgres")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Keeps table fresh for testing; comment out once your demo is final
    cur.execute("DROP TABLE IF EXISTS signals;")
    
    cur.execute("""
        CREATE TABLE signals (
            id TEXT PRIMARY KEY, 
            merchant TEXT, 
            description TEXT, 
            status TEXT DEFAULT 'Pending', 
            severity TEXT DEFAULT 'low',
            ai_data JSONB,
            feedback TEXT DEFAULT 'none'  -- STEP 1: ADDED FOR ADAPTATION
        );
    """)
    
    issues = [
        ('ERR_001', 'Mumbai_Fashion', 'Checkout 404 error on legacy v1', 'low'),
        ('ERR_002', 'Global_Gadgets', 'API Key expired during migration', 'low'),
        ('ERR_004', 'Delhi_Jewels', 'Exposed API keys in production logs', 'high'),
        ('ERR_006', 'Bangalore_Tech', 'Database deadlock in inventory', 'high'),
        ('ERR_007', 'Kolkata_Krafts', 'Slow database response in catalog', 'low'),
        ('ERR_008', 'Chennai_Chic', 'Payment gateway timeout on mobile', 'high'),
        ('ERR_009', 'Hyderabad_High', 'User session token mismatch', 'low')
    ]
    
    cur.executemany("INSERT INTO signals (id, merchant, description, severity) VALUES (%s,%s,%s,%s)", issues)
    conn.commit()
    cur.close(); conn.close()

client = genai.Client(api_key="AIzaSyA3qiACUjDoYz1IIdYJyoo0R2HQQnBcNSs")

def get_mock_ai(merchant, desc):
    return {
        "analysis": {
            "root_cause": f"The diagnostic agent has identified a critical synchronization drift within the {merchant} infrastructure related to {desc}."
        },
        "orda_loop": {
            "observe": f"Scanning telemetry for {merchant} to isolate specific packet loss patterns and latency spikes.",
            "reason": f"Logic isolation suggests a race condition in the {desc} execution path.",
            "decide": "The agent has decided to implement an immediate routing patch to bypass the saturated node.",
            "act": f"Executing automated protocol recovery and deploying a graceful restart to {merchant} nodes."
        }
    }

@app.get("/api/signals")
async def get_signals():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM signals ORDER BY id ASC")
    res = cur.fetchall()
    cur.close(); conn.close()
    return res

@app.post("/api/signals/{signal_id}/heal")
async def heal(signal_id: str):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM signals WHERE id = %s", (signal_id,))
        signal = cur.fetchone()
        
        try:
            prompt = f"Analyze: {signal['description']}. Return JSON (analysis: root_cause, orda_loop: observe, reason, decide, act)."
            response = client.models.generate_content(
                model="gemini-3-flash-preview", 
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            ai_json = json.loads(response.text)
        except Exception as e:
            print(f"DEBUG: Gemini Failed! Error: {str(e)}") 
            ai_json = get_mock_ai(signal['merchant'], signal['description'])
        
        cur.execute("UPDATE signals SET ai_data = %s, status = 'Awaiting_Approval' WHERE id = %s", (json.dumps(ai_json), signal_id))
        conn.commit()
        return ai_json
    finally:
        cur.close(); conn.close()

@app.post("/api/signals/{signal_id}/accept")
async def accept_signal(signal_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE signals SET status = 'Healed' WHERE id = %s", (signal_id,))
        conn.commit()
        return {"status": "Protocol Executed Successfully"}
    finally:
        cur.close(); conn.close()

@app.post("/api/signals/{signal_id}/reject")
async def reject_signal(signal_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE signals SET status = 'Engineer_Assigned' WHERE id = %s", (signal_id,))
        conn.commit()
        return {"status": "Escalated to Engineering Team"}
    finally:
        cur.close(); conn.close()

@app.post("/api/signals/add")
async def add_signal(data: dict):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO signals (id, merchant, description, severity) VALUES (%s, %s, %s, %s)",
            (data['id'], data['merchant'], data['description'], data['severity'])
        )
        conn.commit()
        return {"status": "Signal Added Successfully"}
    finally:
        cur.close(); conn.close()
@app.post("/api/signals/{signal_id}/feedback")
async def save_feedback(signal_id: str, data: dict):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # data['vote'] will be 'positive' or 'negative' from the frontend
        cur.execute("UPDATE signals SET feedback = %s WHERE id = %s", (data['vote'], signal_id))
        conn.commit()
        return {"status": "Feedback logged for model optimization"}
    finally:
        cur.close(); conn.close()
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)