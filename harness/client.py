import requests
import json
import time
import os
import csv

PROXY_URL = "http://127.0.0.1:8080/simulations"

if os.path.exists("alphas.txt"):
    with open("alphas.txt", "r") as f:
        ALPHA_EXPRESSIONS = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    ALPHA_EXPRESSIONS = ["rank(close)"]

headers = {"Content-Type": "application/json"}
results = []

MIN_SHARPE = 2.0
MAX_TURNOVER = 1.0

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
    
    if res.status_code == 401:
        print("? ERROR: BRAIN_SESSION_TOKEN has expired!")
        print("Please update the token in GitHub Secrets -> BRAIN_SESSION_TOKEN.")
        exit(1)

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
                    
                    sharpe = train_metrics.get("sharpe", 0.0)
                    fitness = train_metrics.get("fitness", 0.0)
                    turnover = train_metrics.get("turnover", 0.0)
                    returns = train_metrics.get("returns", 0.0)

                    try:
                        sharpe_val = float(sharpe)
                        turnover_val = float(turnover)

                        if sharpe_val >= MIN_SHARPE and turnover_val <= MAX_TURNOVER:
                            quality_status = "QUALIFIED"
                            print(f"? QUALIFIED ALPHA: {expr} (Sharpe: {sharpe_val}, Turnover: {turnover_val})")
                        else:
                            quality_status = "DISQUALIFIED"
                            print(f"?? DISQUALIFIED: Failed minimum criteria (Sharpe: {sharpe_val}, Turnover: {turnover_val})")
                    except (ValueError, TypeError):
                        quality_status = "UNKNOWN"

                    results.append({
                        "alpha": expr,
                        "status": status,
                        "quality": quality_status,
                        "sharpe": sharpe,
                        "fitness": fitness,
                        "turnover": turnover,
                        "returns": returns
                    })
                    break
                time.sleep(5)
    else:
        print(f"Failed ({res.status_code}): {res.text}")

with open("simulation_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["alpha", "status", "quality", "sharpe", "fitness", "turnover", "returns"])
    writer.writeheader()
    writer.writerows(results)

github_summary = os.getenv("GITHUB_STEP_SUMMARY")
if github_summary:
    with open(github_summary, "a") as f:
        f.write("### ?? Alpha Simulation Summary Results\n\n")
        f.write("| Alpha Expression | Status | Quality Gate | Sharpe | Fitness | Turnover | Returns |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for r in results:
            f.write(f"| `{r['alpha']}` | {r['status']} | {r['quality']} | {r['sharpe']} | {r['fitness']} | {r['turnover']} | {r['returns']} |\n")

print("\nSaved simulation_results.csv and updated Step Summary.")
