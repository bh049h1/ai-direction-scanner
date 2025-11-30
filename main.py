from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class SymbolPayload(BaseModel):
    symbol: str
    price: float
    time: str
    trend: float
    momentum: float
    vola: float
    corr: float = 0.0

class SymbolState(BaseModel):
    symbol: str
    price: float
    time: str
    trend: float
    momentum: float
    vola: float
    flow: float
    score: float
    tag: str
    strength: str
    velocity: float

STATE: Dict[str, SymbolState] = {}
HISTORY: Dict[str, List[float]] = {}

def classify_score(score: float) -> tuple[str, str]:
    if score >= 350:
        return ("STRONG UP", "EXTREME")
    if score <= -350:
        return ("STRONG DOWN", "EXTREME")
    if score >= 250:
        return ("STRONG UP", "STRONG")
    if score <= -250:
        return ("STRONG DOWN", "STRONG")
    if score >= 150:
        return ("UP BIAS", "MODERATE")
    if score <= -150:
        return ("DOWN BIAS", "MODERATE")
    if score >= 50:
        return ("UP BIAS", "WEAK")
    if score <= -50:
        return ("DOWN BIAS", "WEAK")
    return ("CHOP", "NONE")

def calculate_velocity(symbol: str, current_score: float) -> float:
    if symbol not in HISTORY:
        HISTORY[symbol] = []
    HISTORY[symbol].append(current_score)
    if len(HISTORY[symbol]) > 5:
        HISTORY[symbol].pop(0)
    if len(HISTORY[symbol]) >= 3:
        recent = HISTORY[symbol][-3:]
        return (recent[-1] - recent[0]) / len(recent)
    return 0.0

@app.post("/tv-webhook")
async def receive_tv(payload: SymbolPayload):
    t = max(-100, min(100, payload.trend))
    m = max(-100, min(100, payload.momentum))
    v = max(-100, min(100, payload.vola))
    f = max(-100, min(100, payload.corr))
    
    score = t + m + v + f
    tag, strength = classify_score(score)
    velocity = calculate_velocity(payload.symbol.upper(), score)
    
    state = SymbolState(
        symbol=payload.symbol,
        price=payload.price,
        time=payload.time,
        trend=t,
        momentum=m,
        vola=v,
        flow=f,
        score=score,
        tag=tag,
        strength=strength,
        velocity=velocity,
    )
    STATE[payload.symbol.upper()] = state
    return {"status": "ok", "symbol": state.symbol, "score": state.score}

@app.get("/")
async def root():
    return {"message": "AI Direction Scanner API", "symbols": len(STATE)}

@app.get("/snapshot")
async def snapshot():
    return list(STATE.values())

@app.get("/hot")
async def hot_movers():
    hot = [s for s in STATE.values() if s.strength == "EXTREME" or abs(s.velocity) > 30]
    hot.sort(key=lambda x: abs(x.score), reverse=True)
    return hot

@app.get("/scalp-setups")
async def scalp_setups():
    setups = [s for s in STATE.values() 
              if abs(s.score) > 200 and abs(s.velocity) > 20 and abs(s.flow) > 40]
    setups.sort(key=lambda x: abs(x.score), reverse=True)
    return setups
```

Click **"Commit new file"**

---

**File 2: `requirements.txt`**

Click "Add file" → "Create new file" → Name it `requirements.txt`

Paste this:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
```

Click **"Commit new file"**

---

**File 3: `Procfile`** (tells Railway how to run your app)

Click "Add file" → "Create new file" → Name it `Procfile` (exactly, no extension)

Paste this:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
