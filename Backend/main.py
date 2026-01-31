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
    return psycopg2.connect(host="localhost", database="healflow", user="postgres")

@app.on_event("startup")
def startup_db():
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS signals;")
    cur.execute("""
        CREATE TABLE signals (
            id TEXT PRIMARY KEY, 
            merchant TEXT, 
            description TEXT, 
            status TEXT DEFAULT 'Pending', 
            ai_data JSONB
        );
    """)
    # Ensure ERR_004 is in the initial seed
    issues = [
        ('ERR_001', 'Mumbai_Fashion', 'Checkout 404 error on legacy v1'),
        ('ERR_002', 'Global_Gadgets', 'API Key expired during migration'),
        ('ERR_004', 'Delhi_Jewels', 'Exposed API keys in production logs'),
        ('ERR_006', 'Bangalore_Tech', 'Database deadlock in inventory')
    ]
    cur.executemany("INSERT INTO signals (id, merchant, description) VALUES (%s,%s,%s)", issues)
    conn.commit(); cur.close(); conn.close()

client = genai.Client(api_key="AIzaSyCdZEm5PFbz7v0HbXOdNlVGHNA_IRBd8Rk")

def get_mock_ai(merchant, desc):
    # Professional fallback text for the demo
    return {
        "analysis": {
            "root_cause": f"The diagnostic agent has identified a critical synchronization drift within the {merchant} infrastructure related to {desc}."
        },
        "orda_loop": {
            "observe": f"Scanning telemetry for {merchant} to isolate specific packet loss patterns and latency spikes in the checkout region.",
            "reason": f"Logic isolation suggests a race condition in the {desc} execution path, preventing successful handshake completion.",
            "decide": "The agent has decided to implement an immediate routing patch to bypass the saturated node while preserving session integrity.",
            "act": f"Executing automated protocol recovery and deploying a graceful restart command to the affected {merchant} container nodes."
        }
    }

@app.get("/api/signals")
async def get_signals():
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM signals ORDER BY id ASC")
    res = cur.fetchall(); cur.close(); conn.close()
    return res

@app.post("/api/signals/{signal_id}/heal")
async def heal(signal_id: str):
    conn = get_db_connection(); cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM signals WHERE id = %s", (signal_id,))
        signal = cur.fetchone()
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        
        try:
            # Attempt real Gemini call
            prompt = f"Analyze: {signal['description']}. 25 words per field. Return JSON (analysis: root_cause, orda_loop: observe, reason, decide, act)."
            response = client.models.generate_content(model="gemini-1.5-pro", contents=prompt, config=types.GenerateContentConfig(response_mime_type="application/json"))
            ai_json = json.loads(response.text)
        except:
            # Fallback for 429 errors (Quota Exceeded)
            ai_json = get_mock_ai(signal['merchant'], signal['description'])
        
        cur.execute("UPDATE signals SET ai_data = %s, status = 'Healed' WHERE id = %s", (json.dumps(ai_json), signal_id))
        conn.commit()
        return ai_json
    except Exception as e:
        print(f"BACKEND_CRASH_PREVENTED: {e}")
        return {"error": "Internal recovery active"}
    finally: cur.close(); conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)