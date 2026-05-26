import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

# ── Load data ──────────────────────────────────────────────────────
profile5 = pd.read_excel('dataset.xlsx', sheet_name='Full_Profile_List_5_updated')
achievements = pd.read_excel('dataset.xlsx', sheet_name='achievements')
achievements = achievements[achievements['Year'] >= 2019].copy()

df = profile5[profile5['StudentID'] > 0].dropna(subset=['StudentID']).copy()

# Recalculate engagement counts (max of profile vs achievements)
re_counts = achievements[achievements['Type'] == 'RE'].groupby('Kean ID').size().rename('ach_RE')
ex_counts = achievements[achievements['Type'] == 'Ex'].groupby('Kean ID').size().rename('ach_EX')
df = df.join(re_counts, on='StudentID').join(ex_counts, on='StudentID')
df['Num_RE']      = df[['Num_RE', 'ach_RE']].max(axis=1).fillna(0)
df['Num_EX']      = df[['Num_EX', 'ach_EX']].max(axis=1).fillna(0)
df['Total_RE_EX'] = df['Num_RE'] + df['Num_EX']
df = df.drop(columns=['ach_RE', 'ach_EX'])

# Outcome flags
job_ids    = set(achievements[achievements['Type'] == 'Professional Offer']['Kean ID'].dropna())
intern_ids = set(achievements[achievements['Type'] == 'Intern']['Kean ID'].dropna())
ro_ids     = set(achievements[achievements['Type'] == 'RO']['Kean ID'].dropna())

df['has_job']     = df['StudentID'].isin(job_ids).astype(int)
df['has_intern']  = df['StudentID'].isin(intern_ids).astype(int)
df['has_ro']      = df['StudentID'].isin(ro_ids).astype(int)
df['is_hispanic'] = (df['Ethnic Descs'] == 'Hispanic/Latino').astype(int)
df['is_female']   = (df['Gender'] == 'F').astype(int)

# ── Total outcomes score (for simple regression) ───────────────────
df['total_outcomes'] = df['has_job'] + df['has_intern'] + df['has_ro']

print('=' * 65)
print('REGRESSION ANALYSIS — COUGAR PATHWAY TO SUCCESS')
print('=' * 65)
print(f'N = {len(df)} students\n')

# ══════════════════════════════════════════════════════════════════
# 1. SIMPLE LINEAR REGRESSION — Total Activities → Total Outcomes
# ══════════════════════════════════════════════════════════════════
print('=' * 65)
print('1. SIMPLE REGRESSION: Total RE+EX → Total Outcomes')
print('=' * 65)

reg_df = df[['Total_RE_EX', 'total_outcomes']].dropna()
X = sm.add_constant(reg_df['Total_RE_EX'])
y = reg_df['total_outcomes']
model = sm.OLS(y, X).fit()

print(f'  N = {len(reg_df)}')
print(f'  R² = {round(model.rsquared, 3)}')
print(f'  Adjusted R² = {round(model.rsquared_adj, 3)}')
print(f'  F-statistic = {round(model.fvalue, 2)}, p = {model.f_pvalue:.4f}')
print(f'  Intercept = {round(model.params["const"], 3)}')
print(f'  Slope (Total_RE_EX) = {round(model.params["Total_RE_EX"], 3)}')
print(f'  p-value (slope) = {model.pvalues["Total_RE_EX"]:.4f}')
print(f'\n  Interpretation: Each additional RE+EX activity is associated')
print(f'  with a {round(model.params["Total_RE_EX"], 3)} increase in predicted outcomes.')

# ══════════════════════════════════════════════════════════════════
# 2. SIMPLE REGRESSION — GPA → Total Outcomes
# ══════════════════════════════════════════════════════════════════
print()
print('=' * 65)
print('2. SIMPLE REGRESSION: GPA → Total Outcomes')
print('=' * 65)

gpa_df = df[['To Term Gpa Ug', 'total_outcomes']].dropna()
X_gpa = sm.add_constant(gpa_df['To Term Gpa Ug'])
y_gpa = gpa_df['total_outcomes']
model_gpa = sm.OLS(y_gpa, X_gpa).fit()

print(f'  N = {len(gpa_df)}')
print(f'  R² = {round(model_gpa.rsquared, 3)}')
print(f'  Adjusted R² = {round(model_gpa.rsquared_adj, 3)}')
print(f'  F-statistic = {round(model_gpa.fvalue, 2)}, p = {model_gpa.f_pvalue:.4f}')
print(f'  Slope (GPA) = {round(model_gpa.params["To Term Gpa Ug"], 3)}')
print(f'  p-value (slope) = {model_gpa.pvalues["To Term Gpa Ug"]:.4f}')
print(f'\n  Activities R² ({round(model.rsquared,3)}) vs GPA R² ({round(model_gpa.rsquared,3)})')
print(f'  Activities are {round(model.rsquared/model_gpa.rsquared,1)}x stronger predictor than GPA.')

# ══════════════════════════════════════════════════════════════════
# 3. LOGISTIC REGRESSION — Activities → Each Outcome (separate)
# ══════════════════════════════════════════════════════════════════
print()
print('=' * 65)
print('3. LOGISTIC REGRESSION — Activities + GPA → Each Outcome')
print('   (Odds Ratios with 95% Confidence Intervals)')
print('=' * 65)

predictors  = ['Total_RE_EX', 'Num_RE', 'Num_EX', 'To Term Gpa Ug', 'is_hispanic', 'is_female']
pred_labels = ['Total RE+EX', 'Num RE only', 'Num EX only', 'GPA', 'Hispanic/Latino', 'Female']

for outcome, col in [('Professional Offer','has_job'), ('Internship','has_intern'), ('Research Outcome','has_ro')]:
    model_df = df[predictors + [col]].dropna()

    # Drop collinear columns for cleaner model — run Total only (not RE+EX separately)
    preds_clean = ['Total_RE_EX', 'To Term Gpa Ug', 'is_hispanic', 'is_female']
    labels_clean = ['Total RE+EX', 'GPA', 'Hispanic/Latino', 'Female']

    X_log = sm.add_constant(model_df[preds_clean].values)
    y_log = model_df[col].values
    log_model = sm.Logit(y_log, X_log).fit(disp=0)

    print(f'\n--- {outcome} (n={len(model_df)}, events={int(y_log.sum())}) ---')
    print(f'  Pseudo R² (McFadden) = {round(log_model.prsquared, 3)}')
    print(f'  {"Predictor":<20} {"OR":>8} {"95% CI":>20} {"p-value":>10} {"Sig":>5}')
    print(f'  {"-"*65}')

    ci = log_model.conf_int()
    for i, label in enumerate(labels_clean):
        idx = i + 1
        OR      = np.exp(log_model.params[idx])
        ci_low  = np.exp(ci[idx, 0])
        ci_high = np.exp(ci[idx, 1])
        pval    = log_model.pvalues[idx]
        sig = '***' if pval < 0.001 else '**' if pval < 0.01 else '*' if pval < 0.05 else 'ns'
        print(f'  {label:<20} {OR:>8.3f} [{ci_low:>6.3f} – {ci_high:>6.3f}] {pval:>10.4f} {sig:>5}')

# ══════════════════════════════════════════════════════════════════
# 4. CHI-SQUARE — Engagement Tier × Each Outcome
# ══════════════════════════════════════════════════════════════════
print()
print('=' * 65)
print("4. CHI-SQUARE — Engagement Tier × Outcome")
print('   (Tests whether outcome rates differ significantly across tiers)')
print('=' * 65)

def tier(x):
    if x == 0:   return '0'
    elif x == 1: return '1'
    elif x == 2: return '2'
    elif x == 3: return '3'
    elif x <= 6: return '4-6'
    else:        return '7+'

df['tier'] = df['Total_RE_EX'].apply(tier)
TIER_ORDER = ['0', '1', '2', '3', '4-6', '7+']

for outcome, col in [('Professional Offer','has_job'), ('Internship','has_intern'), ('Research Outcome','has_ro')]:
    contingency = []
    for t in TIER_ORDER:
        sub = df[df['tier'] == t]
        yes = int(sub[col].sum())
        no  = len(sub) - yes
        contingency.append([yes, no])
    ct = np.array(contingency)
    chi2, p, dof, expected = stats.chi2_contingency(ct)
    n = ct.sum()
    cramers_v = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))
    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'
    effect = 'small' if cramers_v < 0.1 else 'medium' if cramers_v < 0.3 else 'large'
    print(f'\n  {outcome}:')
    print(f'    Chi-square = {chi2:.3f}, df = {dof}, p = {p:.6f} {sig}')
    print(f'    Cramer\'s V = {cramers_v:.3f} ({effect} effect)')

# ══════════════════════════════════════════════════════════════════
# 5. COHEN'S D — GPA: Engaged vs Not Engaged
# ══════════════════════════════════════════════════════════════════
print()
print('=' * 65)
print("5. COHEN'S D — GPA Differences by Engagement")
print('=' * 65)

gpa_col = 'To Term Gpa Ug'
not_eng = df[df['Total_RE_EX'] == 0][gpa_col].dropna()
engaged = df[df['Total_RE_EX'] > 0][gpa_col].dropna()
pooled  = np.sqrt((not_eng.std()**2 + engaged.std()**2) / 2)
d_overall = (engaged.mean() - not_eng.mean()) / pooled
t_stat, t_p = stats.ttest_ind(engaged, not_eng)

print(f'\n  Not Engaged (0 activities): mean GPA = {round(not_eng.mean(),3)}, SD = {round(not_eng.std(),3)}, n = {len(not_eng)}')
print(f'  Engaged (1+ activities):    mean GPA = {round(engaged.mean(),3)}, SD = {round(engaged.std(),3)}, n = {len(engaged)}')
print(f"  Cohen's d = {round(d_overall,3)} ({'small' if abs(d_overall)<0.2 else 'medium' if abs(d_overall)<0.5 else 'large'} effect)")
print(f'  t({len(engaged)+len(not_eng)-2}) = {round(t_stat,3)}, p = {t_p:.6f}')

print(f'\n  Per-tier Cohen\'s d vs Not Engaged:')
print(f'  {"Tier":<15} {"Mean GPA":>10} {"SD":>7} {"n":>5} {"d":>8} {"Effect":>8}')
print(f'  {"-"*55}')

TIER_ORDER_FULL = ['1', '2', '3', '4-6', '7+']
TIER_LABELS_FULL = ['Engaged 1', 'Engaged 2', 'Engaged 3', 'Medium (4-6)', 'Highly (7+)']
for t, label in zip(TIER_ORDER_FULL, TIER_LABELS_FULL):
    sub = df[df['tier'] == t][gpa_col].dropna()
    if len(sub) < 3:
        continue
    pooled_t = np.sqrt((not_eng.std()**2 + sub.std()**2) / 2)
    d_t = (sub.mean() - not_eng.mean()) / pooled_t
    interp = 'small' if abs(d_t) < 0.2 else 'medium' if abs(d_t) < 0.5 else 'large'
    print(f'  {label:<15} {round(sub.mean(),3):>10} {round(sub.std(),3):>7} {len(sub):>5} {round(d_t,3):>8} {interp:>8}')

print(f'\n  Cohen\'s d — Outcome Achievers vs Non-Achievers (GPA):')
print(f'  {"Outcome":<22} {"Ach Mean":>10} {"Non Mean":>10} {"d":>8} {"Effect":>8}')
print(f'  {"-"*60}')
for outcome, col in [('Job Offer','has_job'), ('Internship','has_intern'), ('Research Outcome','has_ro')]:
    ach = df[df[col] == 1][gpa_col].dropna()
    non = df[df[col] == 0][gpa_col].dropna()
    pooled_o = np.sqrt((ach.std()**2 + non.std()**2) / 2)
    d_o = (ach.mean() - non.mean()) / pooled_o
    interp = 'small' if abs(d_o) < 0.2 else 'medium' if abs(d_o) < 0.5 else 'large'
    print(f'  {outcome:<22} {round(ach.mean(),3):>10} {round(non.mean(),3):>10} {round(d_o,3):>8} {interp:>8}')

print()
print('=' * 65)
print('DONE')
print('=' * 65)
