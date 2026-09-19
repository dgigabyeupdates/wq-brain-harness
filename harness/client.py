import requests
import json
import time

PROXY_URL = "http://127.0.0.1:8080/simulations"

ALPHA_EXPRESSIONS = [
    "rank(close)",
    "rank(volume)",
    "-1 * correlation(open, close, 10)"
]

headers = {
    "Content-Type": "application/json"
}

results = []

for idx, expr in enumerate(ALPHA_EXPRESSIONS, 1):
    print(f"\n--- Testing Alpha {idx}/{len(ALPHA_EXPRESSIONS)}: {expr} ---")
    
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
        "regular": expr
    }

    res = requests.post(PROXY_URL, json=payload, headers=headers)
    if res.status_code in [200, 201]:
        location = res.headers.get("Location")
        print(f"Started. Location: {location}")
        
        if location:
            sim_url = location.replace("https://api.worldquantbrain.com/", "http://127.0.0.1:8080/")
            while True:
                poll = requests.get(sim_url).json()
                status = poll.get("status")
                print(f"Status: {status}")
                if status in ["COMPLETE", "ERROR"]:
                    results.append({"alpha": expr, "status": status, "data": poll})
                    break
                time.sleep(5)
        else:
            results.append({"alpha": expr, "status": "SUBMITTED", "data": res.json()})
    else:
        print(f"Failed ({res.status_code}): {res.text}")

print("\n================ FINAL RESULTS SUMMARY ================")
print(json.dumps(results, indent=2))
