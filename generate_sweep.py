import itertools
arg_max_windows = [63, 126, 252]
backfill_windows = [63, 126, 189]
scale_windows = [30, 60, 90]
expressions = []
for w1, w2, w3 in itertools.product(arg_max_windows, backfill_windows, scale_windows):
    expr = f"a=ts_arg_max(rank(snt21neut_mean_360),{w1});group_zscore(ts_backfill(a,{w2})*ts_scale(region_relative_valuation_score_float,{w3}),market)"
    expressions.append(expr)
with open("alphas.txt", "w") as f:
    for expr in expressions:
        f.write(expr + "\n")
print(f"Generated {len(expressions)} alpha variations into alphas.txt!")
