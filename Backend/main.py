from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# This part is CRUCIAL so your React app doesn't get blocked
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Ensure this matches your Vite URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Your real Signal data
signals_db = [
    {"id": 1, "merchant": "MUMBAI_PAY", "description": "GATEWAY_TIMEOUT_504", "status": "pending", "frequency": 88},
    {"id": 2, "merchant": "STEALTH_SAAS", "description": "AUTH_TOKEN_EXPIRED", "status": "pending", "frequency": 14},
    {"id": 3, "merchant": "REDACTED_CORP", "description": "SQL_INJECTION_ATTEMPT", "status": "pending", "frequency": 102}
]

@app.get("/api/signals")
async def get_signals():
    return signals_db

@app.post("/api/heal/{signal_id}")
async def heal_signal(signal_id: int):
    for s in signals_db:
        if s["id"] == signal_id:
            s["status"] = "healed"
    return {"message": f"Signal {signal_id} repaired"}