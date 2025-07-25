import pandas as pd
import glob
import os
import tkinter as tk
from tkinter import filedialog

# File Dialog to choose locations on machine
root = tk.Tk()
root.withdraw()

folder_path = filedialog.askdirectory(title="Select Folder Containing CSV Files")
if not folder_path:
    raise Exception("No folder selected.")

output_file = filedialog.asksaveasfilename(
    title="Save Final CSV As...",
    defaultextension=".csv",
    filetypes=[("CSV files", "*.csv")]
)
if not output_file:
    raise Exception("No save file selected.")

# Expected output columns - These will of course be varying, based off of your use case
expected_columns = [
    'CUSTOMERNUMBER',
    'CUSTOMERFRIENDLYNAME',
    'BILLINGADDRESS1',
    'BILLINGADDRESS2',
    'BILLINGCITY',
    'BILLINGSTATE',
    'BILLINGZIP',
    'LOCATIONNUMBER',
    'CUSTOMERON',
    'PREVIOUSLOCATION',
    'CUSTOMERPREVIOUSOFF',
    'CUSTOMERIDINFO',
    'CUSTOMERIDOWNER',
    'CUSTOMERREFUSEEXEMPT'
]

# Load and combine all CSV files from selected folder
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
dfs = [pd.read_csv(file, dtype=str) for file in csv_files]
combined = pd.concat(dfs, ignore_index=True)

# Normalize column names and fill missing data
combined.columns = combined.columns.str.strip().str.upper()
combined = combined.fillna('')
cols = combined.columns.tolist()

def find_columns_variants(possible_names, columns):
    return list(set([
        cname for cname in columns
        for pname in possible_names
        if pname.upper() == cname.strip().upper() or pname.upper() in cname.strip().upper()
    ]))

# Column name variants for addresses
address1_variants = ['BILLINGADDRESS1', 'BILLING_ADDR1', 'ADDR1', 'ADDRESS1', 'BILLINGADDRESSLINE1', 'BILLINGADDRESS_1']
address2_variants = ['BILLINGADDRESS2', 'BILLING_ADDR2', 'ADDR2', 'ADDRESS2', 'BILLINGADDRESSLINE2', 'BILLINGADDRESS_2']
street_direction_variants = ['STREETDIRECTION', 'STREET_DIR', 'STDIR', 'STREET_DIRECTION']
street_name_variants = ['STREETNAME', 'ST_NAME', 'STREET_NM']
street_designation_variants = ['STREETDESIGNATION', 'STREET_DESIG', 'STDESIG', 'STREET_TYPE', 'STREET_SUFFIX']
street_number_variants = ['LOCATIONSTREETNUMBER', 'STREETNUMBER', 'STNUM', 'LOCSTNUM']
street_dir_extended_variants = ['LOCATIONSTREETDIRECTION', 'STREETDIRECTION', 'STDIR', 'LOCSTDIR']
street_name_extended_variants = ['LOCATIONSTREETNAME', 'STREETNAME', 'STNAME', 'LOCSTNAME']
street_desig_extended_variants = ['LOCATIONSTREETDESIGNATION', 'STREETDESIGNATION', 'STDESIG', 'STREETTYPE', 'STREET_SUFFIX']
unit_number_variants = ['LOCATIONUNITNUMBER', 'UNITNUMBER', 'APTNUMBER', 'UNITNO', 'APTNO']

def find_first_existing_column(variants):
    for v in variants:
        if v in cols:
            return v
    return None

addr1_cols = find_columns_variants(address1_variants, cols)
addr2_cols = find_columns_variants(address2_variants, cols)
street_dir_cols = find_columns_variants(street_direction_variants, cols)
street_name_cols = find_columns_variants(street_name_variants, cols)
street_desig_cols = find_columns_variants(street_designation_variants, cols)

street_num_col = find_first_existing_column(street_number_variants)
street_dir_ext_col = find_first_existing_column(street_dir_extended_variants)
street_name_ext_col = find_first_existing_column(street_name_extended_variants)
street_desig_ext_col = find_first_existing_column(street_desig_extended_variants)
unit_num_col = find_first_existing_column(unit_number_variants)

# Combine address components into billing address fields
if addr1_cols:
    combined['BILLINGADDRESS1'] = combined[addr1_cols].fillna('').agg(' '.join, axis=1).str.strip()
else:
    combined['BILLINGADDRESS1'] = combined.get('BILLINGADDRESS1', '').fillna('')

if addr2_cols:
    combined['BILLINGADDRESS2'] = combined[addr2_cols].fillna('').agg(' '.join, axis=1).str.strip()
else:
    combined['BILLINGADDRESS2'] = combined.get('BILLINGADDRESS2', '').fillna('')

# Combine old style FULLSTREET (if available)
has_old_street_parts = bool(street_dir_cols) and bool(street_name_cols) and bool(street_desig_cols)
if has_old_street_parts:
    combined['FULLSTREET_OLD'] = (
        combined[street_dir_cols].fillna('').agg(' '.join, axis=1).str.strip() + ' ' +
        combined[street_name_cols].fillna('').agg(' '.join, axis=1).str.strip() + ' ' +
        combined[street_desig_cols].fillna('').agg(' '.join, axis=1).str.strip()
    ).str.replace(r'\s+', ' ', regex=True).str.strip()
else:
    combined['FULLSTREET_OLD'] = ''

# Combine extended FULLSTREET
def combine_location_address(row):
    parts = []
    if street_num_col and row[street_num_col].strip():
        parts.append(row[street_num_col].strip())
    if street_dir_ext_col and row[street_dir_ext_col].strip():
        parts.append(row[street_dir_ext_col].strip())
    if street_name_ext_col and row[street_name_ext_col].strip():
        parts.append(row[street_name_ext_col].strip())
    if street_desig_ext_col and row[street_desig_ext_col].strip():
        parts.append(row[street_desig_ext_col].strip())
    combined_address = ' '.join(parts)
    if unit_num_col and row[unit_num_col].strip():
        combined_address += ' ' + row[unit_num_col].strip()
    return combined_address.strip()

combined['FULLSTREET_NEW'] = combined.apply(combine_location_address, axis=1)

# Choose best full street
def choose_fullstreet(row):
    if row['FULLSTREET_NEW']:
        return row['FULLSTREET_NEW']
    elif row['FULLSTREET_OLD']:
        return row['FULLSTREET_OLD']
    return ''

combined['FULLSTREET'] = combined.apply(choose_fullstreet, axis=1)

# Fill BILLINGADDRESS2 if empty
combined['BILLINGADDRESS2'] = combined.apply(
    lambda row: row['FULLSTREET'] if row['BILLINGADDRESS2'].strip() == '' else row['BILLINGADDRESS2'],
    axis=1
)

# Duplicate rows if new address is different
new_rows = []
def duplicate_with_new_address(row):
    if row['FULLSTREET'].strip() and row['FULLSTREET'].strip() != row['BILLINGADDRESS2'].strip():
        new_row = row.copy()
        new_row['BILLINGADDRESS2'] = row['FULLSTREET'].strip()
        new_rows.append(new_row)
combined.apply(duplicate_with_new_address, axis=1)
if new_rows:
    combined = pd.concat([combined, pd.DataFrame(new_rows)], ignore_index=True)

combined.drop(columns=['FULLSTREET', 'FULLSTREET_NEW', 'FULLSTREET_OLD'], inplace=True, errors='ignore')

# Fill CUSTOMERFRIENDLYNAME if missing
valid_names = combined[combined['CUSTOMERFRIENDLYNAME'] != '']
name_map = (
    valid_names.groupby(['LOCATIONNUMBER', 'CUSTOMERNUMBER'])['CUSTOMERFRIENDLYNAME']
    .agg(lambda x: x.mode()[0] if not x.mode().empty else x.iloc[0])
    .to_dict()
)
def fill_friendly(row):
    if row['CUSTOMERFRIENDLYNAME'].strip() == '':
        return name_map.get((row['LOCATIONNUMBER'], row['CUSTOMERNUMBER']), '')
    return row['CUSTOMERFRIENDLYNAME']
combined['CUSTOMERFRIENDLYNAME'] = combined.apply(fill_friendly, axis=1)

# Ensure all expected columns exist and order the dataframe
for col in expected_columns:
    if col not in combined.columns:
        combined[col] = ''
combined = combined[expected_columns]

# Save the cleaned and merged CSV
combined.to_csv(output_file, index=False)
print(f"Done! Final CSV saved to: {output_file}")
