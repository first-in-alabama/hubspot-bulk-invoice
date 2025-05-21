import numpy as np

COMPANY_DOMAIN_TEMPLATE = '{0}-{1}.org'  # e.g., FRC-1.org

ASSOCIATE_INVOICE_TO_CONTACT = 177
ASSOCIATE_INVOICE_TO_COMPANY = 179


class InvoiceIdentifier(object):
    def __init__(self, contact: int, company: int):
        self.__contact = contact
        self.__company = company

    @property
    def company(self):
        return self.__company

    @property
    def contact(self):
        return self.__contact

    def __eq__(self, other: any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.contact == other.contact and self.company == other.company

    def __hash__(self) -> int:
        return hash((self.contact, self.company))


class LineItemInput(object):
    def __init__(self, contact: int, company: int, quantity: int, description: str, product: int):
        self.__contact = contact
        self.__company = company
        self.__quantity = quantity
        self.__description = description
        self.__product = product

    @property
    def contact(self):
        return self.__contact

    @property
    def company(self):
        return self.__company

    @property
    def quantity(self):
        return self.__quantity

    @property
    def description(self):
        return self.__description

    @property
    def product(self):
        return self.__product

    def invoice_identifier(self) -> InvoiceIdentifier:
        return InvoiceIdentifier(self.contact, self.company)


class SkuIdentifier(object):
    def __init__(self, sku: str, program: str):
        self.__sku = sku
        self.__program = program

    @property
    def sku(self):
        return self.__sku

    @property
    def program(self):
        return self.__program

    def __eq__(self, other: any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.sku == other.sku and self.program == other.program

    def __hash__(self) -> int:
        return hash((self.sku, self.program))


class InvoiceEntryRow(object):
    def __init__(self, program: str, team_number: int, email: str, created_date: np.datetime64, due_date: np.datetime64):
        self.__email = email.lower()
        self.__created_date = created_date
        self.__due_date = due_date
        self.__program = program
        self.__team_number = team_number

    def to_invoice_input(self, contacts: dict[str, int], companies: dict[str, int]):
        domain = COMPANY_DOMAIN_TEMPLATE.format(
            self.__program.lower(), str(self.__team_number))
        return InvoiceInput(
            contacts[self.__email],
            companies[domain],
            int(self.__created_date.timestamp() * 1000),
            int(self.__due_date.timestamp() * 1000)
        )


class InvoiceInput(object):
    def __init__(self, contact: int, company: int, created_date: int, due_date: int):
        self.__contact = str(contact)
        self.__company = str(company)
        self.__created_date = created_date
        self.__due_date = due_date

    @property
    def contact(self) -> str:
        return self.__contact

    @property
    def company(self) -> str:
        return self.__company

    @property
    def created_date(self) -> int:
        return self.__created_date

    @property
    def due_date(self) -> int:
        return self.__due_date

    def __hash__(self) -> int:
        return hash((self.contact, self.company, self.created_date, self.due_date))

    def __eq__(self, other: any) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.contact == other.contact and self.company == other.company and self.created_date == other.created_date and self.due_date == other.due_date

    def to_invoice_input_body(self) -> dict:
        return {
            'properties': {
                "hs_currency": 'USD',
                "hs_invoice_date": self.created_date,
                "hs_due_date": self.due_date
            },
            'associations': [
                {
                    'to': {
                        'id': self.contact
                    },
                    'types': [
                        {
                            'associationCategory': 'HUBSPOT_DEFINED',
                            'associationTypeId': ASSOCIATE_INVOICE_TO_CONTACT
                        }
                    ]
                },
                {
                    'to': {
                        'id': self.company
                    },
                    'types': [
                        {
                            'associationCategory': 'HUBSPOT_DEFINED',
                            'associationTypeId': ASSOCIATE_INVOICE_TO_COMPANY
                        }
                    ]
                }
            ]
        }
