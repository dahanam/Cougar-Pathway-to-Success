import pandas as pd
import numpy as np
 
# ── Load data ──────────────────────────────────────────────────────
profile5 = pd.read_excel('dataset.xlsx', sheet_name='Full_Profile_List_5_updated')
profile6 = pd.read_excel('dataset.xlsx', sheet_name='Full_Profile_List_6_Graduatedst')
# Note: club sheet loaded only if needed for future cross-referencing
# club = pd.read_excel('dataset.xlsx', sheet_name='club member attendees(2019-2025')
 
# ── Clean profile5 ─────────────────────────────────────────────────
df = profile5[profile5['StudentID'] > 0].dropna(subset=['StudentID']).copy()
 
# ── Build lookup from profile6 to fill any remaining missing values ─
p6 = profile6[profile6['StudentID'] > 0].dropna(subset=['StudentID']).copy()
p6 = p6.set_index('StudentID')
 
def fill_from_p6(row, col):
    """Return value from profile6 if available and profile5 value is missing."""
    if pd.isna(row[col]) and row['StudentID'] in p6.index:
        val = p6.loc[row['StudentID'], col]
        return val if not pd.isna(val) else row[col]
    return row[col]
 
for col in ['Gender', 'Race Descs', 'Ethnic Descs', 'Graduation Term']:
    df[col] = df.apply(lambda row: fill_from_p6(row, col), axis=1)
 
# ── Flag what's still missing after cross-referencing ─────────────
df['Missing_Gender']    = df['Gender'].isna()
df['Missing_Race']      = df['Race Descs'].isna()
df['Missing_Ethnicity'] = df['Ethnic Descs'].isna()
df['Missing_Grad']      = df['Graduation Term'].isna()
df['Missing_Any_Demo']  = df['Missing_Gender'] | df['Missing_Race'] | df['Missing_Ethnicity']
 
# ── Filter to students with at least one missing field ─────────────
missing = df[df['Missing_Grad'] | df['Missing_Any_Demo']].copy()
 
# ── Select and order columns ───────────────────────────────────────
output = missing[[
    'StudentID', 'FirstName', 'LastName',
    'Gender', 'Race Descs', 'Ethnic Descs',
    'Start Term Ug', 'Graduation Term',
    'Missing_Gender', 'Missing_Race', 'Missing_Ethnicity', 'Missing_Grad'
]].copy()
 
# ── Summary ────────────────────────────────────────────────────────
total = len(df)
print(f'Total students: {total}')
print(f'After cross-referencing profile6:')
print(f'  Still missing Gender:      {df["Missing_Gender"].sum()} ({round(df["Missing_Gender"].sum()/total*100,1)}%)')
print(f'  Still missing Race:        {df["Missing_Race"].sum()} ({round(df["Missing_Race"].sum()/total*100,1)}%)')
print(f'  Still missing Ethnicity:   {df["Missing_Ethnicity"].sum()} ({round(df["Missing_Ethnicity"].sum()/total*100,1)}%)')
print(f'  Still missing Grad Term:   {df["Missing_Grad"].sum()} ({round(df["Missing_Grad"].sum()/total*100,1)}%)')
print(f'  Missing any demo:          {df["Missing_Any_Demo"].sum()} ({round(df["Missing_Any_Demo"].sum()/total*100,1)}%)')
print(f'  Total flagged (grad or demo missing): {len(output)}')
print()
print(f'  Missing grad only:   {(df["Missing_Grad"] & ~df["Missing_Any_Demo"]).sum()}')
print(f'  Missing demo only:   {(df["Missing_Any_Demo"] & ~df["Missing_Grad"]).sum()}')
print(f'  Missing both:        {(df["Missing_Grad"] & df["Missing_Any_Demo"]).sum()}')
 
# ── Race breakdown ─────────────────────────────────────────────────
print()
print('--- Race Breakdown (all students) ---')
print(df['Race Descs'].value_counts(dropna=False).to_string())
 
# ── Ethnicity breakdown ────────────────────────────────────────────
print()
print('--- Ethnicity Breakdown (all students) ---')
print(df['Ethnic Descs'].value_counts(dropna=False).to_string())
 
# ── Print full list of students with missing data ─────────────────
print()
print('--- Students with Missing Grad or Demographic Data ---')
print(output.to_string(index=False))