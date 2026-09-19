import os
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

app = FastAPI()

BRAIN_EMAIL = os.getenv("BRAIN_EMAIL")
BRAIN_PASSWORD = os.getenv("BRAIN_PASSWORD")
BRAIN_SESSION_TOKEN = os.getenv("BRAIN_SESSION_TOKEN")

session = requests.Session()

def init_session():
    if BRAIN_SESSION_TOKEN:
        session.cookies.set("t", BRAIN_SESSION_TOKEN, domain=".worldquantbrain.com")
        return

    if BRAIN_EMAIL and BRAIN_PASSWORD:
        auth_url = "https://api.worldquantbrain.com/authentication"
        res = session.post(auth_url, auth=(BRAIN_EMAIL, BRAIN_PASSWORD))
        if res.status_code != 201:
            raise Exception(f"BRAIN Auth Failed: {res.text}")

try:
    init_session()
except Exception as e:
    print(f"Warning during session initialization: {e}")

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    target_url = f"https://api.worldquantbrain.com/{path}"
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    body = await request.body()

    res = session.request(
        method=request.method,
        url=target_url,
        headers=headers,
        data=body,
        params=request.query_params
    )

    if res.status_code == 401 and not BRAIN_SESSION_TOKEN:
        try:
            init_session()
            res = session.request(
                method=request.method,
                url=target_url,
                headers=headers,
                data=body,
                params=request.query_params
            )
        except Exception:
            pass

    return JSONResponse(status_code=res.status_code, content=res.json() if res.content else {})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
