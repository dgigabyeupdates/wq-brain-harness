import time
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="WorldQuant BRAIN Local Harness Proxy")

BRAIN_AUTH_URL = "https://api.worldquantbrain.com/authentication"
BRAIN_SIM_URL = "https://api.worldquantbrain.com/simulations"

class SimulationRequest(BaseModel):
    email: str
    password: str
    code: str
    region: str = "USA"
    universe: str = "TOP3000"
    decay: int = 20
    neutralization: str = "SUBINDUSTRY"
    truncation: float = 0.05

@app.post("/simulate")
def run_simulation(req: SimulationRequest):
    session = requests.Session()
    auth_resp = session.post(BRAIN_AUTH_URL, auth=(req.email, req.password))
    if auth_resp.status_code not in [200, 201]:
        raise HTTPException(status_code=401, detail=f"BRAIN Auth Failed: {auth_resp.text}")
    
    simulation_payload = {
        "type": "REGULAR",
        "settings": {
            "instrumentType": "EQUITY",
            "region": req.region,
            "universe": req.universe,
            "delay": 1,
            "decay": req.decay,
            "neutralization": req.neutralization,
            "truncation": req.truncation,
            "pasteurization": "ON",
            "unitHandling": "VERIFY",
            "nanHandling": "OFF",
            "language": "FASTEXPR"
        },
        "code": req.code.strip()
    }

    sim_resp = session.post(BRAIN_SIM_URL, json=simulation_payload)
    if sim_resp.status_code not in [200, 201]:
        raise HTTPException(status_code=sim_resp.status_code, detail=f"Submission Error: {sim_resp.text}")
    
    progress_url = sim_resp.headers.get("Location")
    if not progress_url:
        raise HTTPException(status_code=500, detail="Missing Location header.")

    for _ in range(30):
        poll_resp = session.get(progress_url)
        if poll_resp.status_code == 200:
            status_data = poll_resp.json()
            if status_data.get("status") == "COMPLETE":
                alpha_id = status_data.get("alpha")
                alpha_resp = session.get(f"https://api.worldquantbrain.com/alphas/{alpha_id}")
                if alpha_resp.status_code == 200:
                    is_stats = alpha_resp.json().get("is", {})
                    return {
                        "status": "SUCCESS",
                        "alpha_id": alpha_id,
                        "sharpe": is_stats.get("sharpe", 0.0),
                        "fitness": is_stats.get("fitness", 0.0),
                        "turnover": is_stats.get("turnover", 0.0)
                    }
                return {"status": "SUCCESS", "alpha_id": alpha_id}
        time.sleep(5)

    raise HTTPException(status_code=504, detail="Polling timed out.")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
