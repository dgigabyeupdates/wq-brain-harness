import requests
import json
import time

PROXY_URL = "http://127.0.0.1:8080/simulations"

payload = {
    "type": "REGULAR",
    "settings": {
        "instrumentType": "EQUITY",
        "region": "USA",
        "universe": "TOP3000",
        "delay": 1,
        "decay": 0,
        "neutralization": "SUBINDUSTRY",
        "truncation": 0.08,
        "pasteurization": "ON",
        "unitHandling": "VERIFY",
        "nanHandling": "OFF",
        "language": "FASTEXPR",
        "visualization": False
    },
    "regular": "rank(close)"
}

headers = {
    "Content-Type": "application/json"
}

print("Sending simulation request...")
response = requests.post(PROXY_URL, json=payload, headers=headers)

if response.status_code in [200, 201]:
    location = response.headers.get("Location")
    print(f"Simulation started! Monitor URL: {location}")
    
    if location:
        sim_progress_url = location.replace("https://api.worldquantbrain.com/", "http://127.0.0.1:8080/")
        while True:
            res = requests.get(sim_progress_url)
            data = res.json()
            status = data.get("status")
            print(f"Status: {status}")
            if status in ["COMPLETE", "ERROR"]:
                print("--- SIMULATION COMPLETE ---")
                print(json.dumps(data, indent=2))
                break
            time.sleep(5)
    else:
        print("--- SIMULATION SUCCESSFUL ---")
        print(response.json())
else:
    print(f"FAIL: {response.status_code} - {response.text}")
    exit(1)
