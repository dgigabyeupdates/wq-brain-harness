import requests
import json
import time
import os
import csv

PROXY_URL = "http://127.0.0.1:8080/simulations"

ALPHA_EXPRESSIONS = [
    "rank(close)",
    "rank(volume)",
    "-1 * correlation(open, close, 10)"
]

headers = {"Content-Type": "application/json"}
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
        if location:
            sim_url = location.replace("https://api.worldquantbrain.com/", "http://127.0.0.1:8080/")
            while True:
                poll = requests.get(sim_url).json()
                status = poll.get("status")
                print(f"Status: {status}")
                if status in ["COMPLETE", "ERROR"]:
                    train_metrics = poll.get("train", {})
                    results.append({
                        "alpha": expr,
                        "status": status,
                        "sharpe": train_metrics.get("sharpe", "N/A"),
                        "fitness": train_metrics.get("fitness", "N/A"),
                        "turnover": train_metrics.get("turnover", "N/A"),
                        "returns": train_metrics.get("returns", "N/A")
                    })
                    break
                time.sleep(5)
    else:
        print(f"Failed ({res.status_code}): {res.text}")

with open("simulation_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["alpha", "status", "sharpe", "fitness", "turnover", "returns"])
    writer.writeheader()
    writer.writerows(results)

github_summary = os.getenv("GITHUB_STEP_SUMMARY")
if github_summary:
    with open(github_summary, "a") as f:
        f.write("### ?? Alpha Simulation Summary Results\n\n")
        f.write("| Alpha Expression | Status | Sharpe | Fitness | Turnover | Returns |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in results:
            f.write(f"| `{r['alpha']}` | {r['status']} | {r['sharpe']} | {r['fitness']} | {r['turnover']} | {r['returns']} |\n")

print("\nSaved simulation_results.csv and updated Step Summary.")
