import pandas as pd
import numpy as np
 
# ── Load data ──────────────────────────────────────────────────────
profile5 = pd.read_excel('dataset.xlsx', sheet_name='Full_Profile_List_5_updated')
achievements = pd.read_excel('dataset.xlsx', sheet_name='achievements')
 
# Filter achievements to 2019+ only
achievements = achievements[achievements['Year'] >= 2019].copy()
 
df = profile5[profile5['StudentID'] > 0].dropna(subset=['StudentID']).copy()
 
# Recalculate engagement counts from achievements (take max of profile vs achievements)
re_counts = achievements[achievements['Type'] == 'RE'].groupby('Kean ID').size().rename('ach_RE')
ex_counts = achievements[achievements['Type'] == 'Ex'].groupby('Kean ID').size().rename('ach_EX')
df = df.join(re_counts, on='StudentID').join(ex_counts, on='StudentID')
df['Num_RE']      = df[['Num_RE', 'ach_RE']].max(axis=1).fillna(0)
df['Num_EX']      = df[['Num_EX', 'ach_EX']].max(axis=1).fillna(0)
df['Total_RE_EX'] = df['Num_RE'] + df['Num_EX']
df = df.drop(columns=['ach_RE', 'ach_EX'])
 
# Outcome flags from filtered achievements
job_ids    = set(achievements[achievements['Type'] == 'Job Offer']['Kean ID'].dropna())
intern_ids = set(achievements[achievements['Type'] == 'Intern']['Kean ID'].dropna())
ro_ids     = set(achievements[achievements['Type'] == 'RO']['Kean ID'].dropna())
 
df['has_job']    = df['StudentID'].isin(job_ids).astype(int)
df['has_intern'] = df['StudentID'].isin(intern_ids).astype(int)
df['has_ro']     = df['StudentID'].isin(ro_ids).astype(int)
 
# ── 1. Mean profile: achievers vs non-achievers ───────────────────
print('=' * 60)
print('MEAN PROFILE: ACHIEVERS VS NON-ACHIEVERS')
print('=' * 60)
for outcome, col in [('Job Offer','has_job'), ('Internship','has_intern'), ('Research Outcome','has_ro')]:
    yes = df[df[col] == 1]
    no  = df[df[col] == 0]
    print(f'\n--- {outcome} (n achievers={len(yes)}) ---')
    print(f'  Mean RE:          achievers={round(yes["Num_RE"].mean(),2):>6}  non={round(no["Num_RE"].mean(),2):>6}')
    print(f'  Mean EX:          achievers={round(yes["Num_EX"].mean(),2):>6}  non={round(no["Num_EX"].mean(),2):>6}')
    print(f'  Mean Total RE+EX: achievers={round(yes["Total_RE_EX"].mean(),2):>6}  non={round(no["Total_RE_EX"].mean(),2):>6}')
    print(f'  Mean GPA:         achievers={round(yes["To Term Gpa Ug"].mean(),2):>6}  non={round(no["To Term Gpa Ug"].mean(),2):>6}')
 
# ── 2. Outcome rate by exact Total_RE_EX count ────────────────────
print()
print('=' * 60)
print('OUTCOME RATE BY EXACT TOTAL RE+EX COUNT')
print('=' * 60)
print(f'{"RE+EX":>6} {"N":>5} {"Job%":>7} {"Intern%":>9} {"RO%":>7}')
print('-' * 40)
for n in range(0, 20):
    sub = df[df['Total_RE_EX'] == n]
    if len(sub) < 3:
        continue
    print(f'{n:>6} {len(sub):>5} {round(sub["has_job"].mean()*100,1):>7} {round(sub["has_intern"].mean()*100,1):>9} {round(sub["has_ro"].mean()*100,1):>7}')
 
# ── 3. Students who achieved ALL 3 outcomes ───────────────────────
print()
print('=' * 60)
print('STUDENTS WHO ACHIEVED ALL 3 OUTCOMES')
print('=' * 60)
all3 = df[(df['has_job'] == 1) & (df['has_intern'] == 1) & (df['has_ro'] == 1)]
print(f'Count: {len(all3)}')
print(f'Mean RE:    {round(all3["Num_RE"].mean(), 2)}')
print(f'Mean EX:    {round(all3["Num_EX"].mean(), 2)}')
print(f'Mean Total: {round(all3["Total_RE_EX"].mean(), 2)}')
print(f'Mean GPA:   {round(all3["To Term Gpa Ug"].mean(), 2)}')
print()
print(all3[['FirstName','LastName','Num_RE','Num_EX','Total_RE_EX','To Term Gpa Ug']]
      .sort_values('Total_RE_EX', ascending=False)
      .to_string(index=False))