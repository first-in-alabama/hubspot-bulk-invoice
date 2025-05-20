from argparse import ArgumentParser
import os
from pprint import pprint
from hubspot import Client
import numpy as np
import pandas

SPREADSHEET_VALID_MESSAGE = 'PROBABLY GOOD'

INVOICE_START_DATE = pandas.to_datetime('2025-05-01')
INVOICE_END_DATE = pandas.to_datetime('2026-04-30')

PROGRAMS = set(['FRC', 'FTC', 'FLL', 'JFLL'])

TOKEN_PATH = './secrets/HUBSPOT_API_KEY'
COMPANY_DOMAIN_TEMPLATE = '{}-{}.org' # e.g., FRC-1.org
CREATED_DATE = 'created'
DUE_DATE = 'due'
PROGRAM = 'program'
TEAM_NUMBER = 'number'
EMAIL = 'email'
SKU = 'sku'
QUANTITY = 'quantity'
DESCRIPTION = 'description'
VALID = 'valid'


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
      names=[CREATED_DATE, DUE_DATE, PROGRAM, TEAM_NUMBER, EMAIL, SKU, QUANTITY, DESCRIPTION, VALID],
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
  missing_records = df.isna().any().drop(DESCRIPTION)
  if missing_records[CREATED_DATE]:
    print('Missing one or more invoice created dates')
  if missing_records[DUE_DATE]:
    print('Missing one or more invoice due dates')
  if missing_records[PROGRAM]:
    print('Missing one or more programs')
  if missing_records[TEAM_NUMBER]:
    print('Missing one or more team numbers')
  if missing_records[EMAIL]:
    print('Missing one or more emails')
  if missing_records[SKU]:
    print('Missing one or more product SKUs')
  if missing_records[QUANTITY]:
    print('Missing one or more product quantities')

  if missing_records.any():
    return None
  
  if (df[CREATED_DATE] < INVOICE_START_DATE).any() or (df[CREATED_DATE] > INVOICE_END_DATE).any():
    print('Invoices must be created between', pandas.to_datetime(INVOICE_START_DATE).date(), 'and', pandas.to_datetime(INVOICE_END_DATE).date())
    return None
  
  if (df[DUE_DATE] < INVOICE_START_DATE).any() or (df[DUE_DATE] > INVOICE_END_DATE).any():
    print('Invoices must be due between', pandas.to_datetime(INVOICE_START_DATE).date(), 'and', pandas.to_datetime(INVOICE_END_DATE).date())
    return None
  
  if (df[DUE_DATE] < df[CREATED_DATE]).any():
    print('Invoices must be due ON OR AFTER their creation date')
    return None
  
  programs = set(df[PROGRAM].unique())
  if len(programs.difference(PROGRAMS)) > 0:
    print('Team Program must be one of:', ', '.join(PROGRAMS))
    return None
  
  if (df[TEAM_NUMBER] <= 0).any() or not all(x.is_integer() for x in df[TEAM_NUMBER]):
    print('Team numbers must be positive integers')
    return None
  
  if (df[EMAIL] == '').any():
    print('Emails must be specified')
    return None
  
  if (df[SKU] == '').any():
    print('Product SKUs must be specified')
    return None
  
  if (df[QUANTITY] <= 0).any() or not all(x.is_integer() for x in df[TEAM_NUMBER]):
    print('Product quantities must be positive integers')
    return None
  
  if (df[VALID] != SPREADSHEET_VALID_MESSAGE).any():
    print('One or more spreadsheet validations failed. Check the document and try again')
    return None

  print('Importing', df.shape[0], 'row(s)')

  return df


'''
Using the email addresses, find the Contact IDs
'''
def get_contact_ids(client: Client, emails: set[str]) -> dict:
  return {}


'''
Using the company domains, find the Company IDs
'''
def get_company_ids(client: Client, domains: set[str]) -> dict:
  return {}


'''
Using the product SKUs, find the Product IDs
'''
def get_product_ids(client: Client, skus: set[tuple[str]]) -> dict:
  return {}


'''
Using the quantities, product IDs, and descriptions, create the needed line items.
'''
def create_line_items(client: Client, rows: list, products: dict) -> dict:
  return {}


'''
Using the companies, contacts, line items, and other properties, create the requested invoices.
'''
def create_invoices(client: Client, rows: list, line_items: dict, companies: dict, contacts: dict) -> dict:
  return {}


'''
Extract token from secrets file.
'''
def get_hubspot_api_token() -> str:
  api_token = None
  try:
    with open(TOKEN_PATH) as f: api_token = f.read()
  except:
    api_token = None
  return api_token if api_token is None else api_token.strip()


'''
Execute the sequence of steps to bulk-create invoices from the template spreadsheet.
'''
def main(file_path: str):
  if not os.path.isfile(file_path):
    print('Provided file (', file_path, ') does not exist', sep='')
    return

  print('Beginning upload process...')

  api_token = get_hubspot_api_token()
  if api_token is None:
    print('Could not retrieve HubSpot API token')
    return

  # 1. Parse all data in spreadsheet rows. Exit on error.
  entries = get_rows(file_path)
  if entries is None:
    print('Unable to parse spreadsheet')
    return
  
  # Parse out the key identifiers
  email_addresses = set(entries[EMAIL].tolist())
  if len(email_addresses) == 0:
    print('No emails provided')
    return

  team_domains = set([x for x in entries[PROGRAM] + '-' + entries[TEAM_NUMBER].astype(int).astype(str) + '.org'])
  if len(team_domains) == 0:
    print('No team details provided')
    return
  
  product_skus = set(list(zip(entries[SKU],entries[PROGRAM])))
  if len(product_skus) == 0:
    print('No product SKUs provided')
    return
    
  api_client = Client.create(access_token=api_token)
  
  # 2. Lookup contact by emails. Exit on error.
  contacts = get_contact_ids(api_client, email_addresses)
  if contacts is None:
    print('Unable to lookup the requested contacts')
    return
  
  # 3. Lookup companies by domain. Exit on error.
  companies = get_company_ids(api_client, team_domains)
  if companies is None:
    print('Unable to lookup the requested companies')
    return
  
  # 4. Lookup products by SKU. Exit on error.
  products = get_product_ids(api_client, product_skus)
  if products is None:
    print('Unable to lookup the requested products')
    return
  
  # 5. Create all line items. Exit on error but report successes.
  line_items = create_line_items(api_client, entries, products)
  if line_items is None:
    print('Unable to create the needed line items')
    return
  
  # 6. Create all invoices as drafts. Exit on error but report successes.
  invoices = create_invoices(api_client, entries, line_items, companies, contacts)
  if invoices is None:
    print('Unable to create invoices')
    return
  
  pprint(invoices)

  print('Bulk upload complete!')

if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument("-f", "--file", dest="filepath", help="path to file to read", metavar="FILE")
  args = parser.parse_args()
  if args.filepath is None:
    print('File path was not provided')
  else:
    main(args.filepath)