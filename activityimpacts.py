import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
 
DATASET_PATH = 'dataset.xlsx'
 
NAVY   = '#1B2A4A'
ORANGE = '#E8600A'
GREEN  = '#2a9d5c'
TEAL   = '#1a7a8a'
SLATE  = '#8494ae'
CREAM  = '#F7F4EF'
 
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
achievements = pd.read_excel(DATASET_PATH, sheet_name='achievements')
achievements = achievements[achievements['Year'] >= 2019].copy()  # filter pre-2019
 
profile5 = pd.read_excel('dataset.xlsx', sheet_name='Full_Profile_List_5_updated')
 
df = profile5[profile5['StudentID'] > 0].dropna(subset=['StudentID']).copy()
 
job_ids    = set(achievements[achievements['Type'] == 'Professional Offer']['Kean ID'].dropna())
intern_ids = set(achievements[achievements['Type'] == 'Intern']['Kean ID'].dropna())
ro_ids     = set(achievements[achievements['Type'] == 'RO']['Kean ID'].dropna())
 
df['has_job']    = df['StudentID'].isin(job_ids).astype(int)
df['has_intern'] = df['StudentID'].isin(intern_ids).astype(int)
df['has_ro']     = df['StudentID'].isin(ro_ids).astype(int)
 
# ── Build activity impact table (raw counts) ───────────────────────
rows = []
for act_type in ['Ex', 'RE']:
    activities = achievements[achievements['Type'] == act_type]['Activtiy Name'].value_counts()
    activities = activities[activities >= 5].index
    for act in activities:
        students_did = set(achievements[achievements['Activtiy Name'] == act]['Kean ID'].dropna())
        did_df = df[df['StudentID'].isin(students_did)]
        if len(did_df) < 5:
            continue
        rows.append({
            'Activity': act,
            'Type':     act_type,
            'N':        len(did_df),
            'Job_n':    int(did_df['has_job'].sum()),
            'Intern_n': int(did_df['has_intern'].sum()),
            'RO_n':     int(did_df['has_ro'].sum()),
        })
 
all_df = pd.DataFrame(rows)
 
re_df = all_df[all_df['Type'] == 'RE'].nlargest(10, 'Job_n').sort_values('Job_n')
ex_df = all_df[all_df['Type'] == 'Ex'].nlargest(12, 'Job_n').sort_values('Job_n')
 
# ── Semester/year lookup for EX activities ─────────────────────────
achievements['Sem_Label'] = achievements['Semester'].str.strip() + ' ' + achievements['Year'].astype(str)
semester_lookup = (
    achievements[achievements['Type'] == 'Ex']
    .groupby('Activtiy Name')['Sem_Label']
    .agg(lambda x: x.mode()[0] if len(x) > 0 else 'Unknown')
)
 
def wrap(label, width=28):
    words = label.split()
    lines, line = [], ''
    for w in words:
        if len(line) + len(w) + 1 <= width:
            line = (line + ' ' + w).strip()
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    return '\n'.join(lines)
 
def save(fig, path):
    fig.savefig(path, dpi=180, bbox_inches='tight', facecolor=CREAM)
    plt.close(fig)
    print(f"Saved {path}")
 
def watermark(ax):
    ax.text(0.99, 0.01, 'Cougar Pathway to Success · Kean University',
            transform=ax.transAxes, fontsize=7, color=SLATE,
            ha='right', va='bottom', style='italic')
 
# ══════════════════════════════════════════════════════════════════
# Chart 1: RE Activities
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(13, 7))
y = np.arange(len(re_df))
w = 0.25
 
ax.barh(y - w, re_df['Job_n'],    w, color=NAVY,   label='Professional Offer (students)', edgecolor='white')
ax.barh(y,     re_df['Intern_n'], w, color=ORANGE, label='Internship (students)', edgecolor='white')
ax.barh(y + w, re_df['RO_n'],     w, color=GREEN,  label='Research Outcome (students)', edgecolor='white')
 
for i, (_, row) in enumerate(re_df.iterrows()):
    ax.text(row['Job_n']    + 0.3, i - w, str(int(row['Job_n'])),    va='center', fontsize=8, color=NAVY,   fontweight='bold')
    ax.text(row['Intern_n'] + 0.3, i,     str(int(row['Intern_n'])), va='center', fontsize=8, color=ORANGE, fontweight='bold')
    ax.text(row['RO_n']     + 0.3, i + w, str(int(row['RO_n'])),     va='center', fontsize=8, color=GREEN,  fontweight='bold')
    ax.text(-0.5, i, f'n={int(row["N"])}', va='center', ha='right', fontsize=7.5, color=SLATE)
 
ax.set_yticks(y)
ax.set_yticklabels([wrap(a) for a in re_df['Activity']], fontsize=9)
ax.set_xlabel('Number of Students Achieving Outcome', fontsize=10)
ax.set_title('Most Impactful RE (Research Experience) Activities\nRanked by Number of Students with Professional Offers',
             fontsize=13, fontweight='bold', color=NAVY, pad=14)
ax.legend(fontsize=9, framealpha=0.9, loc='lower right')
ax.set_xlim(-5, 80)
ax.set_axisbelow(True)
watermark(ax)
plt.tight_layout()
save(fig, './activity_impact_RE.png')
 
# ══════════════════════════════════════════════════════════════════
# Chart 2: EX Activities with semester/year
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(13, 9))
y = np.arange(len(ex_df))
 
ax.barh(y - w, ex_df['Job_n'],    w, color=NAVY,   label='Professional Offer (students)', edgecolor='white')
ax.barh(y,     ex_df['Intern_n'], w, color=ORANGE, label='Internship (students)', edgecolor='white')
ax.barh(y + w, ex_df['RO_n'],     w, color=GREEN,  label='Research Outcome (students)', edgecolor='white')
 
for i, (_, row) in enumerate(ex_df.iterrows()):
    ax.text(row['Job_n']    + 0.3, i - w, str(int(row['Job_n'])),    va='center', fontsize=8, color=NAVY,   fontweight='bold')
    ax.text(row['Intern_n'] + 0.3, i,     str(int(row['Intern_n'])), va='center', fontsize=8, color=ORANGE, fontweight='bold')
    ax.text(row['RO_n']     + 0.3, i + w, str(int(row['RO_n'])),     va='center', fontsize=8, color=GREEN,  fontweight='bold')
    ax.text(-0.5, i, f'n={int(row["N"])}', va='center', ha='right', fontsize=7.5, color=SLATE)
 
ax.set_yticks(y)
ax.set_yticklabels(
    [f'{wrap(a)}\n({semester_lookup.get(a, "Unknown")})' for a in ex_df['Activity']],
    fontsize=8.5
)
ax.set_xlabel('Number of Students Achieving Outcome', fontsize=10)
ax.set_title('Most Impactful EX (Engagement) Activities\nRanked by Number of Students with Professional Offers',
             fontsize=13, fontweight='bold', color=NAVY, pad=14)
ax.legend(fontsize=9, framealpha=0.9, loc='lower right')
ax.set_xlim(-5, 35)
ax.set_axisbelow(True)
watermark(ax)
plt.tight_layout()
save(fig, './activity_impact_EX.png')
 
# ══════════════════════════════════════════════════════════════════
# Chart 3: Bubble map
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(13, 8))
 
for _, row in all_df.iterrows():
    color = TEAL if row['Type'] == 'RE' else ORANGE
    ax.scatter(row['Job_n'], row['RO_n'], s=row['N'] * 8,
               color=color, alpha=0.6, edgecolors='white', linewidth=0.8)
 
notable = all_df[(all_df['Job_n'] >= 8) | (all_df['Intern_n'] >= 8) | (all_df['RO_n'] >= 25)]
for _, row in notable.iterrows():
    ax.annotate(wrap(row['Activity'], 20),
                xy=(row['Job_n'], row['RO_n']),
                xytext=(8, 4), textcoords='offset points',
                fontsize=7, color=NAVY,
                arrowprops=dict(arrowstyle='-', color=SLATE, lw=0.8))
 
ax.set_xlabel('Number of Students with Professional Offer', fontsize=11)
ax.set_ylabel('Number of Students with Research Outcome', fontsize=11)
ax.set_title('Activity Impact Map: Professional Offers vs Research Outcomes\n(Bubble size = number of students, color = activity type)',
             fontsize=13, fontweight='bold', color=NAVY, pad=14)
 
re_patch = mpatches.Patch(color=TEAL,   alpha=0.7, label='RE (Research Experience)')
ex_patch = mpatches.Patch(color=ORANGE, alpha=0.7, label='EX (Engagement)')
ax.legend(handles=[re_patch, ex_patch], fontsize=10, framealpha=0.9)
ax.set_axisbelow(True)
watermark(ax)
plt.tight_layout()
save(fig, './activity_impact_bubble.png')
 
# ══════════════════════════════════════════════════════════════════
# Chart 4: ROI — Outcomes per student vs attendance
# ══════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(11, 7))
 
ex_all = all_df[all_df['Type'] == 'Ex'].copy()
ex_all['Total_Outcomes']  = ex_all['Job_n'] + ex_all['Intern_n'] + ex_all['RO_n']
ex_all['ROI_per_student'] = ex_all['Total_Outcomes'] / ex_all['N']
 
ax.scatter(ex_all['N'], ex_all['ROI_per_student'],
           s=ex_all['Total_Outcomes'] * 20,
           color=ORANGE, alpha=0.6, edgecolors='white', linewidth=0.8)
 
for _, row in ex_all.iterrows():
    if row['ROI_per_student'] >= 0.3 or row['N'] >= 20:
        ax.annotate(wrap(row['Activity'], 20),
                    xy=(row['N'], row['ROI_per_student']),
                    xytext=(8, 4), textcoords='offset points',
                    fontsize=7, color=NAVY,
                    arrowprops=dict(arrowstyle='-', color=SLATE, lw=0.8))
 
z = np.polyfit(ex_all['N'], ex_all['ROI_per_student'], 1)
p = np.poly1d(z)
x_line = np.linspace(ex_all['N'].min(), ex_all['N'].max(), 100)
ax.plot(x_line, p(x_line), '--', color=TEAL, linewidth=1.5, label='Trend')
 
ax.set_xlabel('Number of Students Attended (n)', fontsize=11)
ax.set_ylabel('Outcomes per Student (Professional + Intern + RO / n)', fontsize=11)
ax.set_title('Does Higher Attendance Lead to Better Outcomes?\nEX Activities — Outcomes per Student vs Attendance',
             fontsize=13, fontweight='bold', color=NAVY, pad=14)
ax.legend(fontsize=9, framealpha=0.9)
ax.set_axisbelow(True)
watermark(ax)
plt.tight_layout()
save(fig, './activity_impact_ROI.png')
 
print("\nDone! All 4 charts saved.")