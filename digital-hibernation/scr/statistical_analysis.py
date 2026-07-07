#!/usr/bin/env python3
import numpy as np
from scipy import stats

# بيانات menu (10 تكرارات)
menu = [664.74, 637.85, 603.21, 583.92, 574.13, 569.30, 564.19, 558.91, 554.88, 550.26]
# بيانات teo (10 تكرارات)
teo = [550.98, 545.47, 542.58, 542.55, 540.31, 536.82, 537.11, 535.59, 533.93, 533.54]
# بيانات expected_cost (محسوبة من نسبة الـ regret)
expected = [418.67] * 10  # متوسط

print("=" * 60)
print("STATISTICAL ANALYSIS")
print("=" * 60)

def stats_summary(name, data):
    mean = np.mean(data)
    std = np.std(data, ddof=1)
    ci_low = mean - 1.96 * std / np.sqrt(len(data))
    ci_high = mean + 1.96 * std / np.sqrt(len(data))
    print(f"{name:>16}: {mean:.2f} ± {std:.2f} J, 95% CI [{ci_low:.2f}, {ci_high:.2f}]")
    return mean, std

print("\n[Summary]")
m_mean, m_std = stats_summary("menu", menu)
t_mean, t_std = stats_summary("teo", teo)
e_mean, e_std = stats_summary("Expected-Cost", expected)

print("\n[Statistical Tests]")
t, p = stats.ttest_ind(menu, expected)
print(f"menu vs Expected-Cost: t = {t:.2f}, p = {p:.6f}")
t, p = stats.ttest_ind(menu, teo)
print(f"menu vs teo: t = {t:.2f}, p = {p:.6f}")

print("\n[Savings]")
savings_exp = (m_mean - e_mean) / m_mean * 100
savings_teo = (m_mean - t_mean) / m_mean * 100
print(f"Expected-Cost savings vs menu: {savings_exp:.2f}%")
print(f"teo savings vs menu: {savings_teo:.2f}%")