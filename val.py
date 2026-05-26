import pandas as pd
 
# ── Load data ──────────────────────────────────────────────────────
profile5 = pd.read_excel('dataset.xlsx', sheet_name='Full_Profile_List_5_updated')
profile6     = pd.read_excel('dataset.xlsx', sheet_name='Full_Profile_List_6_Graduatedst')
achievements = pd.read_excel('dataset.xlsx', sheet_name='achievements')
si_nso       = pd.read_excel('dataset.xlsx', sheet_name='si_nso_data')
 
# Filter achievements to 2019+ only
achievements = achievements[achievements['Year'] >= 2019].copy()
 
df = profile5[profile5['StudentID'] > 0].dropna(subset=['StudentID']).copy()
 
def tier(x):
    if x == 0:   return '0 - Not Engaged'
    elif x == 1: return '1 - Engaged 1'
    elif x == 2: return '2 - Engaged 2'
    elif x == 3: return '3 - Engaged 3'
    elif x <= 6: return '4 - Medium (4-6)'
    else:        return '5 - Highly (7+)'
 
df['tier'] = df['Total_RE_EX'].apply(tier)
 
# Ethnicity: standardized to 'Hispanic/Latino' in updated CSV
df['is_hispanic'] = (df['Ethnic Descs'] == 'Hispanic/Latino').astype(int)
df['is_female']   = (df['Gender'] == 'F').astype(int)
df['is_male']     = (df['Gender'] == 'M').astype(int)
df['is_both']     = ((df['is_hispanic'] == 1) & (df['is_female'] == 1)).astype(int)
 
job_ids    = set(achievements[achievements['Type'] == 'Job Offer']['Kean ID'].dropna())
intern_ids = set(achievements[achievements['Type'] == 'Intern']['Kean ID'].dropna())
ro_ids     = set(achievements[achievements['Type'] == 'RO']['Kean ID'].dropna())
award_ids  = set(achievements[achievements['Type'] == 'Award']['Kean ID'].dropna())
grad_ids   = set(profile6['StudentID'].dropna())
 
df['has_job']    = df['StudentID'].isin(job_ids).astype(int)
df['has_intern'] = df['StudentID'].isin(intern_ids).astype(int)
df['has_ro']     = df['StudentID'].isin(ro_ids).astype(int)
df['has_award']  = df['StudentID'].isin(award_ids).astype(int)
df['graduated']  = df['StudentID'].isin(grad_ids).astype(int)
 
# ── 1. Total students ─────────────────────────────────────────────
print('=' * 55)
print('TOTAL UNIQUE STUDENTS:', len(df))
print('=' * 55)
 
# ── 2. Engagement tiers ───────────────────────────────────────────
print('\n--- Engagement Tiers ---')
tier_counts = df['tier'].value_counts().sort_index()
for t, n in tier_counts.items():
    print(f'  {t}: {n}')
print(f'  TOTAL: {tier_counts.sum()}')
 
# ── 3. Gender ─────────────────────────────────────────────────────
print('\n--- Gender ---')
print(f'  Male:    {df["is_male"].sum()}')
print(f'  Female:  {df["is_female"].sum()}')
print(f'  Unknown: {(df["Gender"].isna() | ~df["Gender"].isin(["M","F"])).sum()}')
 
# ── 4. Ethnicity ──────────────────────────────────────────────────
print('\n--- Ethnicity ---')
print(f'  Hispanic/Latino:     {df["is_hispanic"].sum()}')
print(f'  Non-Hispanic/Latino: {(df["Ethnic Descs"] == "Non Hispanic/Latino").sum()}')
print(f'  Unknown/Blank:       {df["Ethnic Descs"].isna().sum()}')
print(f'  Both Hispanic+Female:{df["is_both"].sum()}')
 
# ── 5. Race breakdown ─────────────────────────────────────────────
print('\n--- Race ---')
print(df['Race Descs'].value_counts(dropna=False).to_string())
 
# ── 6. Outcomes (unique students) ─────────────────────────────────
print('\n--- Unique Students with Outcomes ---')
print(f'  Job Offer:        {df["has_job"].sum()}')
print(f'  Internship:       {df["has_intern"].sum()}')
print(f'  Research Outcome: {df["has_ro"].sum()}')
print(f'  Award:            {df["has_award"].sum()}')
print(f'  Graduated:        {df["graduated"].sum()}')
 
# ── 7. Engagement activity counts (unique students) ───────────────
print('\n--- Unique Students with Engagement Activities ---')
re_ids = set(achievements[achievements['Type'] == 'RE']['Kean ID'].dropna())
ex_ids = set(achievements[achievements['Type'] == 'Ex']['Kean ID'].dropna())
df['has_re'] = df['StudentID'].isin(re_ids).astype(int)
df['has_ex'] = df['StudentID'].isin(ex_ids).astype(int)
print(f'  RE (Research Exp):  {df["has_re"].sum()}')
print(f'  EX (Engagement):    {df["has_ex"].sum()}')
print(f'  Both RE and EX:     {((df["has_re"]==1) & (df["has_ex"]==1)).sum()}')
 
# ── 8. Total activity rows (non-unique, 2019+) ────────────────────
print('\n--- Total Activity Rows in Achievements (non-unique, 2019+) ---')
for t, n in achievements['Type'].value_counts().items():
    print(f'  {t}: {n}')
print(f'  TOTAL ROWS: {len(achievements)}')
 
# ── 9. SI/NSO ─────────────────────────────────────────────────────
print('\n--- SI/NSO Total Records ---')
for t, n in si_nso['Type'].value_counts().items():
    print(f'  {t}: {n}')
print(f'  TOTAL ROWS: {len(si_nso)}')
 
# ── 10. GPA summary ───────────────────────────────────────────────
print('\n--- GPA Summary (students with GPA data) ---')
gpa = df['To Term Gpa Ug'].dropna()
print(f'  Students with GPA: {len(gpa)}')
print(f'  Mean:   {round(gpa.mean(), 3)}')
print(f'  Median: {round(gpa.median(), 3)}')
print(f'  Min:    {round(gpa.min(), 3)}')
print(f'  Max:    {round(gpa.max(), 3)}')
 
# ── 11. Max engagement per student ────────────────────────────────
print('\n--- Engagement Range ---')
print(f'  Min Total_RE_EX: {int(df["Total_RE_EX"].min())}')
print(f'  Max Total_RE_EX: {int(df["Total_RE_EX"].max())}')
top = df.nlargest(3, 'Total_RE_EX')[['FirstName','LastName','Total_RE_EX','Num_RE','Num_EX']]
print('  Top 3 most engaged students:')
for _, r in top.iterrows():
    print(f'    {r["FirstName"]} {r["LastName"]}: {int(r["Total_RE_EX"])} (RE={int(r["Num_RE"])}, EX={int(r["Num_EX"])})')