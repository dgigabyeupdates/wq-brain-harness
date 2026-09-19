import os
import requests

EMAIL = os.getenv("BRAIN_EMAIL")
PASSWORD = os.getenv("BRAIN_PASSWORD")
HARNESS_URL = "http://127.0.0.1:8080/simulate"

ALPHA_CODE = "stats=generate_stats([rank(close/open),group_rank(ts_decay_linear(returns,10),sector),ts_zscore(vwap,60),rank(vec_avg(scl12_sentiment)),rank(vec_avg(snt1_cored1_score)),rank(vec_avg(anl69_best_net_numest)),group_neutralize(ts_rank(returns,120),industry),rank(close-low),rank(high-close),ts_rank(adv20,20),rank(ts_std_dev(returns,20)),rank(cap)]); weight=1-reduce_norm(self_corr(stats.drawdown,120)); scale_down(ts_mean(weight,15))"

payload = {
    "email": EMAIL,
    "password": PASSWORD,
    "code": ALPHA_CODE,
    "region": "USA",
    "universe": "TOP3000",
    "decay": 20,
    "neutralization": "SUBINDUSTRY",
    "truncation": 0.05
}

response = requests.post(HARNESS_URL, json=payload)

if response.status_code == 200:
    res = response.json()
    alpha_id = res.get("alpha_id")
    sharpe = res.get("sharpe")
    fitness = res.get("fitness")
    print("--- SIMULATION SUCCESSFUL ---")
    print(f"Alpha ID: {alpha_id}")
    print(f"Sharpe: {sharpe}")
    print(f"Fitness: {fitness}")
else:
    print(f"FAIL: {response.status_code} - {response.text}")
    exit(1)
