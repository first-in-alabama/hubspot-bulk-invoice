from argparse import ArgumentParser
import os
from pprint import pprint
from hubspot import Client
from api import create_invoices, create_line_items, get_company_ids, get_contact_ids, get_product_ids
from excel_import import CREATED_DATE_COL, DESCRIPTION_COL, DUE_DATE_COL, EMAIL_COL, PROGRAM_COL, QUANTITY_COL, SKU_COL, TEAM_NUMBER_COL, get_rows
from invoice_input import COMPANY_DOMAIN_TEMPLATE, InvoiceEntryRow, LineItemInput, SkuIdentifier

TOKEN_PATH = './secrets/HUBSPOT_API_KEY'


def get_hubspot_api_token() -> str:
    '''Extract token from secrets file.'''
    api_token = None
    try:
        with open(TOKEN_PATH) as f:
            api_token = f.read()
    except:
        api_token = None
    return api_token if api_token is None else api_token.strip()


def main(file_path: str):
    '''Execute the sequence of steps to bulk-create invoices from the template spreadsheet.'''
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
    email_addresses = set([str(x)
                          for x in entries[EMAIL_COL].astype(str).tolist()])
    if len(email_addresses) == 0:
        print('No emails provided')
        return

    team_domains = set([COMPANY_DOMAIN_TEMPLATE.format(x, y) for x, y in zip(
        entries[PROGRAM_COL].str.lower(), entries[TEAM_NUMBER_COL].astype(int).astype(str))])
    if len(team_domains) == 0:
        print('No team details provided')
        return

    product_skus = set([SkuIdentifier(str(x), str(y)) for x, y in zip(
        entries[SKU_COL].astype(str), entries[PROGRAM_COL].astype(str))])
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

    # 5. Create all invoices as drafts. Exit on error but report successes.
    invoice_hubspot_values = set([
        InvoiceEntryRow(program, team_number, email, created_date,
                        due_date).to_invoice_input(contacts, companies)
        for email, program, team_number, created_date, due_date
        in zip(entries[EMAIL_COL], entries[PROGRAM_COL], entries[TEAM_NUMBER_COL], entries[CREATED_DATE_COL], entries[DUE_DATE_COL])
    ])

    invoices = create_invoices(api_client, invoice_hubspot_values)
    if invoices is None:
        print('Unable to generate the requested invoices')
        return

    # 6. Create all line items for invoices. Exit on error but report successes.
    line_item_inputs = [
        LineItemInput(contacts[email], companies[COMPANY_DOMAIN_TEMPLATE.format(
            str(prog).lower(), number)], int(qty), desc, products[sku])
        for sku, qty, desc, prog, number, email in
        zip(entries[SKU_COL], entries[QUANTITY_COL].astype(int), entries[DESCRIPTION_COL], entries[PROGRAM_COL].astype(
            str), entries[TEAM_NUMBER_COL].astype(int).astype(str), entries[EMAIL_COL])
    ]

    line_items = create_line_items(api_client, line_item_inputs, invoices)
    if line_items is None:
        print('Unable to create the needed line items')
        return

    print('Bulk upload complete for the invoices listed below!')
    pprint([x for x in invoices.values()])


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-f", "--file", dest="filepath",
                        help="path to file to read", metavar="FILE")
    args = parser.parse_args()
    if args.filepath is None:
        print('File path was not provided')
    else:
        main(args.filepath)
