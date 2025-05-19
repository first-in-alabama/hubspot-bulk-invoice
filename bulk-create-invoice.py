from argparse import ArgumentParser
import os
from pprint import pprint
from hubspot import Client

TOKEN_PATH = './secrets/HUBSPOT_API_KEY'
COMPANY_DOMAIN_TEMPLATE = '{}-{}.org' # e.g., FRC-1.org


'''
Parse the entries in the spreadsheet template
'''
def get_rows() -> list:
  return []


'''
Using the email addresses, find the Contact IDs
'''
def get_contact_ids(client: Client, rows: list) -> dict:
  return {}


'''
Using the company domains, find the Company IDs
'''
def get_company_ids(client: Client, rows: list) -> dict:
  return {}


'''
Using the product SKUs, find the Product IDs
'''
def get_product_ids(client: Client, rows: list) -> dict:
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
  entries = get_rows()
  if entries is None:
    print('Unable to parse spreadsheet')
    return
  
  api_client = Client.create(access_token=api_token)
  
  # 2. Lookup contact by emails. Exit on error.
  contacts = get_contact_ids(api_client, entries)
  if contacts is None:
    print('Unable to lookup the requested contacts')
    return
  
  # 3. Lookup companies by domain. Exit on error.
  companies = get_company_ids(api_client, entries)
  if companies is None:
    print('Unable to lookup the requested companies')
    return
  
  # 4. Lookup products by SKU. Exit on error.
  products = get_product_ids(api_client, entries)
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