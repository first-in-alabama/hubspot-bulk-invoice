from pprint import pprint
from hubspot import Client
import requests

from invoice_input import InvoiceIdentifier, InvoiceInput, LineItemInput, SkuIdentifier

SEASONS_API = 'https://my.firstinspires.org/usfirstapi/seasons/search'


def fetch_first_seasons() -> dict[str, int]:
    '''Get the current seasons for all FIRST programs'''
    seasons = None
    try:
        seasons = {s['ProgramCode']: int(s['SeasonYearStart']) for s in requests.get(
            SEASONS_API).json() if s['IsCurrentSeason']}
    except:
        print('Unable to retrieve current seasons from FIRST')
        seasons = None
    return seasons


def get_contact_ids(client: Client, emails: set[str]) -> dict[str, int]:
    '''Using the email addresses, find the Contact IDs'''
    print('Asking HubSpot for Contact IDs...')
    email_lookup = [{'id': email} for email in emails]
    body = {
        'idProperty': 'email',
        'inputs': email_lookup
    }

    api_response = None
    try:
        api_response = client.crm.contacts.batch_api.read(
            batch_read_input_simple_public_object_id=body)
    except Exception as e:
        pprint(e)
        print('Unable to query the Contacts from HubSpot')
        api_response = None

    if api_response is None:
        return None
    if hasattr(api_response, 'errors') or not hasattr(api_response, 'results'):
        print('There were one or more errors associated with the Contact FETCH call')
        pprint(api_response)
        return None

    results = None
    try:
        results = {x.properties['email']: int(
            x.id) for x in api_response.results if not x.archived}
    except:
        print('One or more errors occurred when reading the Contact lookup results')
        results = None

    if results is None or len(results) == 0:
        print('Could not find any Contacts')
        return None

    missing_emails = emails.difference(set(results.keys()))
    if missing_emails:
        print('One or more emails could not be found for active contacts:',
              ', '.join(missing_emails))
        return None

    print('Retrieved Contact IDs!')
    return results


def get_company_ids(client: Client, domains: set[str]) -> dict[str, int]:
    '''Using the company domains, find the Company IDs'''
    print('Asking HubSpot for Company IDs...')
    body = {
        'filterGroups': [
            {
                'filters': [
                    {
                        'propertyName': 'domain',
                        'operator': 'IN',
                        'values': list(domains)
                    }
                ]
            }
        ],
        'properties': ['id', 'domain']
    }

    api_response = None
    try:
        api_response = client.crm.companies.search_api.do_search(
            public_object_search_request=body)
    except Exception as e:
        pprint(e)
        print('Unable to query the Companies from HubSpot')
        api_response = None

    if api_response is None:
        return None
    if hasattr(api_response, 'errors') or not hasattr(api_response, 'results'):
        print('There were one or more errors associated with the Company FETCH call')
        pprint(api_response)
        return None

    results = None
    try:
        results = {x.properties['domain']: int(
            x.id) for x in api_response.results if not x.archived}
    except:
        print('One or more errors occurred when reading the Company lookup results')
        results = None

    if results is None or len(results) == 0:
        print('Could not find any Company')
        return None

    missing_domains = domains.difference(set(results.keys()))
    if missing_domains:
        print('One or more domains could not be found for active companies:',
              ', '.join(missing_domains))
        return None

    print('Retrieved Company IDs!')
    return results


def get_product_ids(client: Client, skus: list[SkuIdentifier]) -> dict[SkuIdentifier, int]:
    '''Using the product SKUs, find the Product IDs'''
    print('Asking HubSpot for Product IDs...')
    program_codes = set([x.program for x in skus])
    sku_keys = set([x.sku for x in skus])
    current_seasons = fetch_first_seasons()
    if len(program_codes) == 0 or current_seasons is None:
        print('Unable to check seasonalities of one or more products')
        return None

    body = {
        'filterGroups': [
            {
                'filters': [
                    {
                        'propertyName': 'hs_sku',
                        'operator': 'IN',
                        'values': list(sku_keys)
                    }
                ]
            }
        ],
        'properties': ['season_year', 'program', 'hs_sku']
    }

    api_response = None
    try:
        api_response = client.crm.products.search_api.do_search(
            public_object_search_request=body)
    except Exception as e:
        pprint(e)
        print('Unable to query the Products from HubSpot')
        api_response = None

    if api_response is None:
        return None
    if hasattr(api_response, 'errors') or not hasattr(api_response, 'results'):
        print('There were one or more errors associated with the Product FETCH call')
        pprint(api_response)
        return None

    results: dict[int, SkuIdentifier] = None
    try:
        results = {
            int(x.id): SkuIdentifier(str(x.properties['hs_sku']), str(x.properties['program']))
            for x in api_response.results
            if not x.archived and str(current_seasons[x.properties['program']]) == x.properties['season_year']
        }
    except:
        print('One or more errors occurred when reading the Product lookup results. Verify that all SKUs are for the correct program and season')
        results = None

    if results is None or len(results) == 0:
        print('Could not find any Product')
        return None

    missing_skus = set(skus).difference(set(results.values()))
    if missing_skus:
        print(
            'One or more SKUs/Program combinations could not be found for active products.')
        print(
            'It could be that the SKU does not exist, so double check the HubSpot listing.')
        print('It could also be that the SKU is not valid for the current season.')
        print('The current season is based on the year when the program kicks off (e.g., FRC January, FTC September)')
        print('Verify that the missing SKUs are aligned with the correct program in the spreadsheet.')
        print('Check these records (SKUs are case sensitive).')
        print('\n'.join(['\t{0} in {1}'.format(x.sku, x.program)
              for x in missing_skus]))
        return None

    print('Retrieved Product IDs!')
    return {v: k for k, v in results.items()}


def create_invoices(client: Client, invoice_values: list[InvoiceInput]) -> dict[InvoiceIdentifier, int]:
    '''Using the companies, contacts, and other properties, create the requested invoices.'''
    print('Asking HubSpot to generate the Invoices...')
    invoice_body = {
        'inputs': [
            x.to_invoice_input_body()
            for x in invoice_values
        ]
    }

    api_response = None
    try:
        api_response = client.crm.commerce.invoices.batch_api.create(
            batch_input_simple_public_object_batch_input_for_create=invoice_body)
    except Exception as e:
        pprint(e)
        print('Unable to generate the Invoices from HubSpot')
        api_response = None

    if api_response is None:
        return None
    if hasattr(api_response, 'errors') or not hasattr(api_response, 'results'):
        print('There were one or more errors associated with the Invoice CREATE call')
        pprint(api_response)
        return None

    invoice_ids = None
    try:
        invoice_ids = set([int(x.id)
                          for x in api_response.results if not x.archived])
    except:
        print('One or more errors occurred when creating Invoices')
        invoice_ids = None

    if invoice_ids is None or len(invoice_ids) == 0:
        print('Could not create any Invoice')
        return None

    if len(invoice_values) != len(invoice_ids):
        print('One or more invoices was not generated. Please clear the records from HubSpot, check your data source, and try again')
        return None

    associations_body = {
        'inputs': [
            {
                'id': x
            } for x in invoice_ids
        ]
    }

    invoice_to_contacts: dict[int, int] = {}
    try:
        contact_result = client.crm.associations.batch_api.read(
            '0-53', '0-1', batch_input_public_object_id=associations_body)
        for result in contact_result.results:
            values = result.to_dict()
            invoice_to_contacts[int(values['_from']['id'])] = int(
                values['to'][0]['id'])
    except Exception as e:
        pprint(e)
        print('Unable to match contacts to invoices. Please clear the Invoices from HubSpot, check your data source, and try again')
        return None

    if len(invoice_to_contacts.keys()) == 0:
        print('Unable to match contacts to invoices. Please clear the Invoices from HubSpot, check your data source, and try again')
        return None

    invoice_to_companies: dict[int, int] = {}
    try:
        company_result = client.crm.associations.batch_api.read(
            '0-53', '0-2', batch_input_public_object_id=associations_body)
        for result in company_result.results:
            values = result.to_dict()
            invoice_to_companies[int(values['_from']['id'])] = int(
                values['to'][0]['id'])
    except Exception as e:
        pprint(e)
        print('Unable to match companies to invoices. Please clear the Invoices from HubSpot, check your data source, and try again')
        return None

    if len(invoice_to_companies.keys()) == 0:
        print('Unable to match companies to invoices. Please clear the Invoices from HubSpot, check your data source, and try again')
        return None

    if len(invoice_to_contacts.keys()) != len(invoice_to_companies.keys()):
        print('There was a discrepancy between the invoice to contacts and companies mappings. Please clear the Invoices from HubSpot, check your data source, and try again')
        return None

    associations_lookup: dict[int, InvoiceIdentifier] = {}
    for invoice_id in invoice_ids:
        associations_lookup[invoice_id] = InvoiceIdentifier(invoice_to_contacts[invoice_id],
                                                            invoice_to_companies[invoice_id])

    print('Generated', len(associations_lookup), 'Invoices!')
    return {v: k for k, v in associations_lookup.items()}


def create_line_items(client: Client, line_items: list[LineItemInput], invoices: dict[InvoiceIdentifier, int]) -> set[int]:
    '''Using the quantities, product IDs, descriptions, and invoices, create the needed line items.'''
    print('Asking HubSpot to apply the Line Items to invoices...')
    line_item_invoice_keys = set([x.invoice_identifier() for x in line_items])
    invoice_keys = set(invoices.keys())

    if len(line_item_invoice_keys.symmetric_difference(invoice_keys)) > 0:
        print('Could not match all invoices with all line items. Please clear the invoices from HubSpot, check your data source, and try again')
        return None

    body = {
        'inputs': [
            {
                'properties': {
                    'quantity': x.quantity,
                    'hs_product_id': x.product,
                    'description': x.description
                },
                'associations': [
                    {
                        'types': [
                            {
                                'associationCategory': 'HUBSPOT_DEFINED',
                                'associationTypeId': 410
                            }
                        ],
                        'to': {
                            'id': invoices[x.invoice_identifier()]
                        }
                    }
                ]
            }
            for x
            in line_items
        ]
    }

    api_response = None
    try:
        api_response = client.crm.line_items.batch_api.create(
            batch_input_simple_public_object_batch_input_for_create=body)
    except Exception as e:
        pprint(e)
        print('Unable to apply the Line Items to the Invoices in HubSpot. Please clear the invoices from HubSpot, check your data source, and try again')
        api_response = None

    if api_response is None:
        return None
    if hasattr(api_response, 'errors') or not hasattr(api_response, 'results'):
        print('There were one or more errors associated with the Line Item CREATE call. Please clear the invoices from HubSpot, check your data source, and try again')
        pprint(api_response)
        return None

    line_item_ids = None
    try:
        line_item_ids = set([int(x.id)
                             for x in api_response.results if not x.archived])
    except:
        print('One or more errors occurred when creating Line Items. Please clear the invoices from HubSpot, check your data source, and try again')
        line_item_ids = None

    if line_item_ids is None or len(line_item_ids) == 0:
        print('Could not create any Line Items')
        return None

    if len(line_item_ids) != len(line_items):
        print('One or more line items was not generated. Please clear the invoices from HubSpot, check your data source, and try again')
        return None

    print('Line Items created and applied!')
    return line_item_ids
