import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
 
# ── Config ─────────────────────────────────────────────────────────
DATASET_PATH = 'dataset.xlsx'
 
NAVY    = '#1B2A4A'
NAVY_L  = '#4a6090'
ORANGE  = '#E8600A'
GREEN   = '#2a9d5c'
TEAL    = '#1a7a8a'
GOLD    = '#c8a227'
SLATE   = '#8494ae'
CREAM   = '#F7F4EF'
 
plt.rcParams.update({
    'font.family': 'DejaVu Sans',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.facecolor': 'white',
    'figure.facecolor': CREAM,
    'axes.grid': True,
    'grid.color': '#e8e0d5',
    'grid.linewidth': 0.6,
    'axes.edgecolor': '#ccc4b8',
    'xtick.color': NAVY,
    'ytick.color': NAVY,
    'text.color': NAVY,
})
 
# ── Load data ──────────────────────────────────────────────────────
print("Loading data...")
achievements_raw = pd.read_excel(DATASET_PATH, sheet_name='achievements')
si_nso           = pd.read_excel(DATASET_PATH, sheet_name='si_nso_data')
profile5         = pd.read_excel('dataset.xlsx', sheet_name='Full_Profile_List_5_updated')
profile6         = pd.read_excel(DATASET_PATH, sheet_name='Full_Profile_List_6_Graduatedst')
 
# ── Filter achievements to 2019+ only ─────────────────────────────
achievements = achievements_raw[achievements_raw['Year'] >= 2019].copy()
 
print(f"Achievements rows: {len(achievements_raw)} total -> {len(achievements)} after pre-2019 filter")
print(f"  Removed {len(achievements_raw) - len(achievements)} records before 2019")
 
# ── Build student-level dataframe ─────────────────────────────────
df = profile5[profile5['StudentID'] > 0].dropna(subset=['StudentID']).copy()
 
# Recalculate Num_RE, Num_EX, Total_RE_EX from filtered achievements
# Take the max of profile5 value vs achievements count so no student loses engagement
re_counts = achievements[achievements['Type'] == 'RE'].groupby('Kean ID').size().rename('ach_RE')
ex_counts = achievements[achievements['Type'] == 'Ex'].groupby('Kean ID').size().rename('ach_EX')
 
df = df.join(re_counts, on='StudentID').join(ex_counts, on='StudentID')
df['Num_RE']      = df[['Num_RE', 'ach_RE']].max(axis=1).fillna(0)
df['Num_EX']      = df[['Num_EX', 'ach_EX']].max(axis=1).fillna(0)
df['Total_RE_EX'] = df['Num_RE'] + df['Num_EX']
df = df.drop(columns=['ach_RE', 'ach_EX'])
 
# Outcome flags from filtered achievements
job_ids    = set(achievements[achievements['Type'] == 'Professional Offer']['Kean ID'].dropna())
intern_ids = set(achievements[achievements['Type'] == 'Intern']['Kean ID'].dropna())
ro_ids     = set(achievements[achievements['Type'] == 'RO']['Kean ID'].dropna())
grad_ids   = set(profile6['StudentID'].dropna())
 
df['has_job']     = df['StudentID'].isin(job_ids).astype(int)
df['has_intern']  = df['StudentID'].isin(intern_ids).astype(int)
df['has_ro']      = df['StudentID'].isin(ro_ids).astype(int)
df['graduated']   = df['StudentID'].isin(grad_ids).astype(int)
df['is_hispanic'] = (df['Ethnic Descs'] == 'Hispanic/Latino').astype(int)
df['is_female']   = (df['Gender'] == 'F').astype(int)
 
print(f"Students in analysis: {len(df)}")
 
def tier(x):
    if x == 0:   return '0'
    elif x == 1: return '1'
    elif x == 2: return '2'
    elif x == 3: return '3'
    elif x <= 6: return '4-6'
    else:        return '7+'
 
df['tier'] = df['Total_RE_EX'].apply(tier)
 
TIER_ORDER  = ['0', '1', '2', '3', '4-6', '7+']
TIER_LABELS = ['Not\nEngaged\n(0)', 'Engaged\n1', 'Engaged\n2', 'Engaged\n3', 'Medium\n(4-6)', 'Highly\n(7+)']
 
# ── Aggregate per tier ─────────────────────────────────────────────
stats = {}
for t in TIER_ORDER:
    sub = df[df['tier'] == t]
    gpa = sub['To Term Gpa Ug'].dropna()
    n = len(sub)
    stats[t] = {
        'n':          n,
        'job_pct':    round(sub['has_job'].sum() / n * 100, 1) if n > 0 else 0,
        'intern_pct': round(sub['has_intern'].sum() / n * 100, 1) if n > 0 else 0,
        'ro_pct':     round(sub['has_ro'].sum() / n * 100, 1) if n > 0 else 0,
        'grad_pct':   round(sub['graduated'].sum() / n * 100, 1) if n > 0 else 0,
        'hisp_pct':   round(sub['is_hispanic'].sum() / n * 100, 1) if n > 0 else 0,
        'female_pct': round(sub['is_female'].sum() / n * 100, 1) if n > 0 else 0,
        'gpa_mean':   round(gpa.mean(), 3) if len(gpa) > 0 else 0,
        'gpa_q1':     round(gpa.quantile(0.25), 3) if len(gpa) > 0 else 0,
        'gpa_q3':     round(gpa.quantile(0.75), 3) if len(gpa) > 0 else 0,
        'gpa_min':    round(gpa.min(), 3) if len(gpa) > 0 else 0,
        'gpa_max':    round(gpa.max(), 3) if len(gpa) > 0 else 0,
    }
 
print("\nTier summary (2019+ filtered):")
for t in TIER_ORDER:
    print(f"  Tier {t}: n={stats[t]['n']}, job={stats[t]['job_pct']}%, intern={stats[t]['intern_pct']}%, ro={stats[t]['ro_pct']}%")
 
def get(key): return [stats[t][key] for t in TIER_ORDER]
 
x = np.arange(len(TIER_ORDER))
 
# ── Activity by year (RQ1) — capped at 2025 for chart only ────────
ach_year = (achievements[achievements['Year'].between(2019, 2025)]
            .groupby(['Year', 'Type']).size().unstack(fill_value=0))
years_rq1 = [str(y) for y in ach_year.index]
 
def ach(col): return list(ach_year[col]) if col in ach_year.columns else [0]*len(years_rq1)
 
# ── SI/NSO by year ─────────────────────────────────────────────────
sinso_year = si_nso.groupby(['Year', 'Type']).size().unstack(fill_value=0)
years_sinso = [str(int(float(y))) for y in sinso_year.index]
si_vals  = list(sinso_year['SI'])  if 'SI'  in sinso_year.columns else []
nso_vals = list(sinso_year['NSO']) if 'NSO' in sinso_year.columns else []
 
# ── Helpers ────────────────────────────────────────────────────────
def save(fig, path):
    fig.savefig(path, dpi=180, bbox_inches='tight', facecolor=CREAM)
    plt.close(fig)
    print(f"Saved {path}")
 
def watermark(ax):
    ax.text(0.99, 0.01, 'Cougar Pathway to Success · Kean University',
            transform=ax.transAxes, fontsize=7, color=SLATE,
            ha='right', va='bottom', style='italic')
 
# ══════════════════════════════════════════════════════════════════
# RQ1 — Chart 1: Stacked activity by year
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(11, 6))
bottom = np.zeros(len(years_rq1))
for col, label, color in [
    ('Ex',        'EX - Engagement',    TEAL),
    ('RO',        'RO - Research Out.', GREEN),
    ('RE',        'RE - Research Exp.', ORANGE),
    ('Professional Offer', 'Professional Offer',          NAVY),
    ('Intern',    'Internship',         GOLD),
    ('Award',     'Award',              '#c97bb2'),
]:
    vals = np.array(ach(col))
    ax.bar(years_rq1, vals, bottom=bottom, label=label, color=color,
           width=0.6, edgecolor='white', linewidth=0.4)
    bottom += vals
 
ax.set_title('RQ1 - Activity Volume by Year and Type', fontsize=14, fontweight='bold', color=NAVY, pad=14)
ax.set_xlabel('Academic Year', fontsize=10)
ax.set_ylabel('Activity Records', fontsize=10)
ax.legend(loc='upper left', fontsize=8.5, framealpha=0.9, ncol=2)
ax.set_axisbelow(True)
watermark(ax)
save(fig, './RQ1_activity_by_year.png')
 
# ══════════════════════════════════════════════════════════════════
# RQ1 — Chart 2: SI / NSO trend
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(9, 5))
xi = np.arange(len(years_sinso))
ax.bar(xi - 0.2, si_vals,  0.35, label='SI (Supplemental Instruction)', color=TEAL,   edgecolor='white')
ax.bar(xi + 0.2, nso_vals, 0.35, label='NSO (New Student Orientation)', color=ORANGE, edgecolor='white')
ax.set_xticks(xi)
ax.set_xticklabels(years_sinso)
ax.set_title('RQ1 - SI & NSO Participation Over Time', fontsize=14, fontweight='bold', color=NAVY, pad=14)
ax.set_xlabel('Year', fontsize=10)
ax.set_ylabel('Participants', fontsize=10)
ax.legend(fontsize=9, framealpha=0.9)
ax.set_axisbelow(True)
watermark(ax)
save(fig, './RQ1_si_nso_trend.png')
 
# ══════════════════════════════════════════════════════════════════
# RQ2 — Chart 1: Grouped outcome rates
# ══════════════════════════════════════════════════════════════════
job_r    = get('job_pct')
intern_r = get('intern_pct')
ro_r     = get('ro_pct')
 
fig, ax = plt.subplots(figsize=(12, 6))
w = 0.25
ax.bar(x - w, job_r,    w, label='Professional Offer %',        color=NAVY,   edgecolor='white')
ax.bar(x,     intern_r, w, label='Internship %',       color=ORANGE, edgecolor='white')
ax.bar(x + w, ro_r,     w, label='Research Outcome %', color=GREEN,  edgecolor='white')
 
for i, (j, ii, r) in enumerate(zip(job_r, intern_r, ro_r)):
    ax.text(i - w, j  + 0.8, f'{j}%',  ha='center', fontsize=7.5, color=NAVY)
    ax.text(i,     ii + 0.8, f'{ii}%', ha='center', fontsize=7.5, color=ORANGE)
    ax.text(i + w, r  + 0.8, f'{r}%',  ha='center', fontsize=7.5, color=GREEN)
 
ax.set_xticks(x)
ax.set_xticklabels(TIER_LABELS, fontsize=9)
ax.set_title('RQ2 - Outcome Rates by Engagement Tier', fontsize=14, fontweight='bold', color=NAVY, pad=14)
ax.set_xlabel('Engagement Tier (Total RE+EX Activities)', fontsize=10)
ax.set_ylabel('% of Students Achieving Outcome', fontsize=10)
ax.legend(fontsize=9, framealpha=0.9)
ax.set_ylim(0, 115)
ax.set_axisbelow(True)
watermark(ax)
save(fig, './RQ2_outcome_rates.png')
 
# ══════════════════════════════════════════════════════════════════
# RQ2 — Chart 2: Job + Internship side by side
# ══════════════════════════════════════════════════════════════════
navy_shades   = ['#d4dae5','#b8c3d4','#8fa4bf','#6685a9','#3d6690','#1B2A4A']
orange_shades = ['#fde8d8','#fbd1b3','#f8b88a','#f5a066','#f28840','#E8600A']
 
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('RQ2 - Career Outcome Rates by Engagement Tier', fontsize=14, fontweight='bold', color=NAVY, y=1.01)
 
bars1 = ax1.bar(TIER_LABELS, job_r, color=navy_shades, edgecolor='white', width=0.6)
for bar, val in zip(bars1, job_r):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{val}%', ha='center', fontsize=9, color=NAVY, fontweight='bold')
ax1.set_title('Professional Offer Rate', fontsize=12, fontweight='bold', color=NAVY)
ax1.set_ylabel('% of Students', fontsize=10)
ax1.set_ylim(0, 80)
ax1.set_axisbelow(True)
watermark(ax1)
 
bars2 = ax2.bar(TIER_LABELS, intern_r, color=orange_shades, edgecolor='white', width=0.6)
for bar, val in zip(bars2, intern_r):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{val}%', ha='center', fontsize=9, color=ORANGE, fontweight='bold')
ax2.set_title('Internship Rate', fontsize=12, fontweight='bold', color=ORANGE)
ax2.set_ylabel('% of Students', fontsize=10)
ax2.set_ylim(0, 50)
ax2.set_axisbelow(True)
watermark(ax2)
 
plt.tight_layout()
save(fig, './RQ2_job_intern_rates.png')
 
# ══════════════════════════════════════════════════════════════════
# RQ3 — Chart 1: GPA IQR + mean line
# ══════════════════════════════════════════════════════════════════
means = get('gpa_mean')
q1s   = get('gpa_q1')
q3s   = get('gpa_q3')
mins  = get('gpa_min')
maxs  = get('gpa_max')
 
fig, ax = plt.subplots(figsize=(10, 6))
for i in range(len(x)):
    ax.bar(i, q3s[i] - q1s[i], bottom=q1s[i], color=ORANGE, alpha=0.18, width=0.5, zorder=2)
    ax.vlines(i, mins[i], maxs[i], color=SLATE, linewidth=1.2, zorder=1, linestyle='--', alpha=0.5)
    ax.hlines([q1s[i], q3s[i]], i - 0.18, i + 0.18, colors=ORANGE, linewidth=1.5, zorder=3)
 
ax.plot(x, means, 'o-', color=NAVY, linewidth=2.5, markersize=8, zorder=4)
for i, m in enumerate(means):
    ax.text(i, m + 0.06, f'{m:.2f}', ha='center', fontsize=9, color=NAVY, fontweight='bold')
 
ax.set_xticks(x)
ax.set_xticklabels(TIER_LABELS, fontsize=9)
ax.set_title('RQ3 - GPA Distribution by Engagement Tier', fontsize=14, fontweight='bold', color=NAVY, pad=14)
ax.set_xlabel('Engagement Tier (Total RE+EX Activities)', fontsize=10)
ax.set_ylabel('Undergraduate GPA', fontsize=10)
ax.set_ylim(1.2, 4.4)
ax.legend(handles=[
    plt.Line2D([0],[0], color=NAVY, linewidth=2.5, marker='o', markersize=7, label='Mean GPA'),
    mpatches.Patch(color=ORANGE, alpha=0.35, label='IQR (25th-75th %ile)')
], fontsize=9, framealpha=0.9)
ax.set_axisbelow(True)
watermark(ax)
save(fig, './RQ3_gpa_distribution.png')
 
# ══════════════════════════════════════════════════════════════════
# RQ3 — Chart 2: Mean GPA + RO rate side by side
# ══════════════════════════════════════════════════════════════════
blue_shades  = ['#dce6f0','#b8cfe3','#8cb3d4','#6097c5','#347ab6','#1B2A4A']
green_shades = ['#c8e6d4','#a0d1b4','#72b892','#44a070','#1a824e','#2a9d5c']
 
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('RQ3 - Academic & Research Achievement by Engagement Tier', fontsize=14, fontweight='bold', color=NAVY, y=1.01)
 
bars1 = ax1.bar(TIER_LABELS, means, color=blue_shades, edgecolor='white', width=0.6)
for bar, val in zip(bars1, means):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
             f'{val:.2f}', ha='center', fontsize=9, color=NAVY, fontweight='bold')
ax1.set_title('Mean GPA', fontsize=12, fontweight='bold', color=NAVY)
ax1.set_ylabel('GPA', fontsize=10)
ax1.set_ylim(2.4, 4.0)
ax1.set_axisbelow(True)
watermark(ax1)
 
bars2 = ax2.bar(TIER_LABELS, ro_r, color=green_shades, edgecolor='white', width=0.6)
for bar, val in zip(bars2, ro_r):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
             f'{val}%', ha='center', fontsize=9, color=GREEN, fontweight='bold')
ax2.set_title('Research Outcome Rate', fontsize=12, fontweight='bold', color=GREEN)
ax2.set_ylabel('% of Students', fontsize=10)
ax2.set_ylim(0, 115)
ax2.set_axisbelow(True)
watermark(ax2)
 
plt.tight_layout()
save(fig, './RQ3_gpa_and_ro.png')
 
# ══════════════════════════════════════════════════════════════════
# RQ4 — Chart 1: Demographics by tier
# ══════════════════════════════════════════════════════════════════
hisp_pct   = get('hisp_pct')
female_pct = get('female_pct')
 
fig, ax = plt.subplots(figsize=(11, 6))
ax.bar(x - 0.2, hisp_pct,   0.35, label='Hispanic/Latino %', color=ORANGE, edgecolor='white')
ax.bar(x + 0.2, female_pct, 0.35, label='Female %',          color=TEAL,   edgecolor='white')
 
for i, (h, f) in enumerate(zip(hisp_pct, female_pct)):
    ax.text(i - 0.2, h + 0.6, f'{h}%', ha='center', fontsize=8, color=ORANGE, fontweight='bold')
    ax.text(i + 0.2, f + 0.6, f'{f}%', ha='center', fontsize=8, color=TEAL,   fontweight='bold')
 
ax.set_xticks(x)
ax.set_xticklabels(TIER_LABELS, fontsize=9)
ax.set_title('RQ4 - Hispanic/Latino & Female Representation by Engagement Tier\n(% of all students in tier)',
             fontsize=13, fontweight='bold', color=NAVY, pad=14)
ax.set_xlabel('Engagement Tier', fontsize=10)
ax.set_ylabel('% of Students in Tier', fontsize=10)
ax.legend(fontsize=9, framealpha=0.9)
ax.set_ylim(0, 115)
ax.set_axisbelow(True)
watermark(ax)
save(fig, './RQ4_demographics.png')
 
# ══════════════════════════════════════════════════════════════════
# RQ4 — Chart 2: Graduation rate + SI/NSO
# ══════════════════════════════════════════════════════════════════
grad_r = get('grad_pct')
navy_shades2 = ['#dce0ea','#bcc4d6','#9aaabf','#7890a8','#507090','#1B2A4A']
 
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle('RQ4 - Retention & Intervention Trends', fontsize=14, fontweight='bold', color=NAVY, y=1.01)
 
bars = ax1.bar(TIER_LABELS, grad_r, color=navy_shades2, edgecolor='white', width=0.6)
for bar, val in zip(bars, grad_r):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
             f'{val}%', ha='center', fontsize=9, color=NAVY, fontweight='bold')
ax1.set_title('Graduation Rate by Engagement Tier', fontsize=12, fontweight='bold', color=NAVY)
ax1.set_ylabel('Graduation Rate %', fontsize=10)
ax1.set_ylim(0, 85)
ax1.set_axisbelow(True)
watermark(ax1)
 
ax2.plot(years_sinso, si_vals,  'o-', color=TEAL,   linewidth=2.5, markersize=7, label='SI')
ax2.plot(years_sinso, nso_vals, 's-', color=ORANGE, linewidth=2.5, markersize=7, label='NSO')
ax2.fill_between(years_sinso, si_vals,  alpha=0.1, color=TEAL)
ax2.fill_between(years_sinso, nso_vals, alpha=0.1, color=ORANGE)
ax2.set_title('SI & NSO Growth as Entry Interventions', fontsize=12, fontweight='bold', color=NAVY)
ax2.set_ylabel('Participants', fontsize=10)
ax2.legend(fontsize=9, framealpha=0.9)
ax2.set_axisbelow(True)
watermark(ax2)
 
plt.tight_layout()
save(fig, './RQ4_graduation_sinso.png')
 
print("\nDone! All 8 charts saved.")
print(f"\nFinal dataset summary:")
print(f"  Total students: {len(df)}")
print(f"  Achievement records used: {len(achievements)} (2019+ only)")
for t in TIER_ORDER:
    print(f"  Tier {t}: n={stats[t]['n']}")
 