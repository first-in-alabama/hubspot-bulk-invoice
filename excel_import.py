import numpy as np
import pandas

CREATED_DATE_COL = 'created'
DUE_DATE_COL = 'due'
PROGRAM_COL = 'program'
TEAM_NUMBER_COL = 'number'
EMAIL_COL = 'email'
SKU_COL = 'sku'
QUANTITY_COL = 'quantity'
DESCRIPTION_COL = 'description'
VALID_COL = 'valid'

SPREADSHEET_VALID_MESSAGE = 'PROBABLY GOOD'

INVOICE_START_DATE = pandas.to_datetime('2025-05-01')
INVOICE_END_DATE = pandas.to_datetime('2026-04-30')

PROGRAMS = set(['FRC', 'FTC', 'FLL', 'JFLL'])


'''
Parse the entries in the spreadsheet template
'''
def get_rows(file_path: str) -> pandas.DataFrame:
  print('Reading spreadsheet...')
  df = None
  try:
    df = pandas.read_excel(
      file_path, 
      usecols='A:I', 
      names=[CREATED_DATE_COL, DUE_DATE_COL, PROGRAM_COL, TEAM_NUMBER_COL, EMAIL_COL, SKU_COL, QUANTITY_COL, DESCRIPTION_COL, VALID_COL],
      dtype={
        'a': np.datetime64,
        'b': np.datetime64,
        'c': str,
        'd': np.int64,
        'e': str,
        'f': str,
        'g': np.int64,
        'h': str,
        'i': str
      }
    ).dropna(how='all')
  except:
    print('Unable to read (alleged) Excel file (', file_path, ')', sep='')
    df = None

  if df is None: return None

  print('Validating rows...')
  missing_records = df.isna().any().drop(DESCRIPTION_COL)
  if missing_records[CREATED_DATE_COL]:
    print('Missing one or more invoice created dates')
  if missing_records[DUE_DATE_COL]:
    print('Missing one or more invoice due dates')
  if missing_records[PROGRAM_COL]:
    print('Missing one or more programs')
  if missing_records[TEAM_NUMBER_COL]:
    print('Missing one or more team numbers')
  if missing_records[EMAIL_COL]:
    print('Missing one or more emails')
  if missing_records[SKU_COL]:
    print('Missing one or more product SKUs')
  if missing_records[QUANTITY_COL]:
    print('Missing one or more product quantities')

  if missing_records.any():
    return None
  
  if (df[CREATED_DATE_COL] < INVOICE_START_DATE).any() or (df[CREATED_DATE_COL] > INVOICE_END_DATE).any():
    print('Invoices must be created between', pandas.to_datetime(INVOICE_START_DATE).date(), 'and', pandas.to_datetime(INVOICE_END_DATE).date())
    return None
  
  if (df[DUE_DATE_COL] < INVOICE_START_DATE).any() or (df[DUE_DATE_COL] > INVOICE_END_DATE).any():
    print('Invoices must be due between', pandas.to_datetime(INVOICE_START_DATE).date(), 'and', pandas.to_datetime(INVOICE_END_DATE).date())
    return None
  
  if (df[DUE_DATE_COL] < df[CREATED_DATE_COL]).any():
    print('Invoices must be due ON OR AFTER their creation date')
    return None
  
  programs = set(df[PROGRAM_COL].unique())
  if len(programs.difference(PROGRAMS)) > 0:
    print('Team Program must be one of:', ', '.join(PROGRAMS))
    return None
  
  if (df[TEAM_NUMBER_COL] <= 0).any() or not all(x.is_integer() for x in df[TEAM_NUMBER_COL]):
    print('Team numbers must be positive integers')
    return None
  
  if (df[EMAIL_COL] == '').any():
    print('Emails must be specified')
    return None
  
  if (df[SKU_COL] == '').any():
    print('Product SKUs must be specified')
    return None
  
  if (df[QUANTITY_COL] <= 0).any() or not all(x.is_integer() for x in df[TEAM_NUMBER_COL]):
    print('Product quantities must be positive integers')
    return None
  
  if (df[VALID_COL] != SPREADSHEET_VALID_MESSAGE).any():
    print('One or more spreadsheet validations failed. Check the document and try again')
    return None
  
  df[EMAIL_COL] = df[EMAIL_COL].str.lower()
  df[DESCRIPTION_COL] = df[DESCRIPTION_COL].fillna('')

  df[CREATED_DATE_COL] = df[CREATED_DATE_COL].dt.tz_localize('America/Chicago')
  df[DUE_DATE_COL] = df[DUE_DATE_COL].dt.tz_localize('America/Chicago')

  print('Importing', df.shape[0], 'row(s)!')

  return df

