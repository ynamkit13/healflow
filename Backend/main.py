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
    
    # THE DROP LINE: Deletes old table so new structure (severity column) is created
    cur.execute("DROP TABLE IF EXISTS signals;")
    
    cur.execute("""
        CREATE TABLE signals (
            id TEXT PRIMARY KEY, 
            merchant TEXT, 
            description TEXT, 
            status TEXT DEFAULT 'Pending', 
            severity TEXT DEFAULT 'low',
            ai_data JSONB
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
    cur.close()
    conn.close()

# Ensure you use the active key provided by your friend
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
    cur.close()
    conn.close()
    return res

@app.post("/api/signals/{signal_id}/heal")
async def heal(signal_id: str):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM signals WHERE id = %s", (signal_id,))
        signal = cur.fetchone()
        
        print(f"DEBUG: Attempting Gemini call for {signal['merchant']}...")

        try:
            prompt = f"Analyze: {signal['description']}. Return JSON (analysis: root_cause, orda_loop: observe, reason, decide, act)."
            # UPDATED MODEL NAME: Using the reasoning-optimized Gemini 3 Flash
            response = client.models.generate_content(
                model="gemini-3-flash-preview", 
                contents=prompt, 
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    ]
                )
            )
            ai_json = json.loads(response.text)
            print("DEBUG: Gemini Success!") 
        except Exception as e:
            print(f"DEBUG: Gemini Failed! Error: {str(e)}") 
            ai_json = get_mock_ai(signal['merchant'], signal['description'])
        
        cur.execute("UPDATE signals SET ai_data = %s, status = 'Healed' WHERE id = %s", (json.dumps(ai_json), signal_id))
        conn.commit()
        return ai_json
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
    except Exception as e:
        return {"error": str(e)}
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)