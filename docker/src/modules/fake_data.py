
import random
import datetime
import polars as pl
from faker import Faker


class FakeData:

    def __init__(self, country:str = 'en_US') -> None:
        self.fake               = Faker(country)
        self.num_records_ass    = 150 * 5
        self.num_records_act    = 300 * 5
        self.num_records_card   = 400 * 5
        self.num_records_mov    = 600 * 5

    def default_base(self) -> dict[str, dict]:
        """
        Generates default base data for associates, accounts, cards, and movements.

        Returns:
            dict[str, dict]: A dictionary containing the generated data for associates, accounts, cards, and movements.
                - 'associate': A dictionary with the following keys:
                    - 'associate_id': List of unique associate IDs.
                    - 'name': List of first names.
                    - 'last_name': List of last names.
                    - 'age': List of ages.
                    - 'email': List of unique email addresses.
                - 'account': A dictionary with the following keys:
                    - 'account_id': List of unique account IDs.
                    - 'account_type': List of account types (Corrente, Poupanca, Personnalite).
                    - 'creation_date': List of account creation dates.
                - 'card': A dictionary with the following keys:
                    - 'card_id': List of unique card IDs.
                    - 'card_number': List of unique card numbers.
                - 'movement': A dictionary with the following keys:
                    - 'movement_id': List of unique movement IDs.
                    - 'vlr_transaction': List of transaction values.
                    - 'des_transaction': List of transaction descriptions (debit, credit).
                    - 'movement_date': List of movement dates.
        """

        self.dict_associate = \
            dict(
                associate_id  = [self.fake.unique.random_int(min=100_000, max=999_999) for _ in range(self.num_records_ass)],
                name          = [self.fake.first_name() for _ in range(self.num_records_ass)],
                last_name     = [self.fake.last_name() for _ in range(self.num_records_ass)],
                age           = [self.fake.random_int(min=18, max=100) for _ in range(self.num_records_ass)],
                email         = [self.fake.unique.free_email() for _ in range(self.num_records_ass)]
            )

        self.dict_account = \
            dict(
                    account_id      = [self.fake.unique.random_int(min=100000, max=999999) for _ in range(self.num_records_act)],
                    account_type    = [random.choice(['Corrente', 'Poupanca', 'Personnalite']) for _ in range(self.num_records_act)],
                    creation_date   = [self.fake.date_between_dates(
                                        date_start=datetime.date(2000, 1, 1),
                                        date_end=datetime.date(2023, 4, 30))for _ in range(self.num_records_act)]
                )

        self.dict_card = \
            dict(
                card_id         = [self.fake.unique.random_int(min=1_000_000, max=9_999_999) for _ in range(self.num_records_card)],
                card_number     = [self.fake.unique.random_int(
                    min=1000_0000_0000_0000,
                    max=9999_9999_9999_9999) for _ in range(self.num_records_card)]
            )

        self.dict_movement = \
            dict(
                movement_id     = [self.fake.unique.random_int(min=100_000_000, max=999_999_999) for _ in range(self.num_records_mov)],
                vlr_transaction = [round(random.uniform(0, 9999), 2) for _ in range(self.num_records_mov)],
                des_transaction = [random.choice(['debit', 'credit']) for _ in range(self.num_records_mov)],
                movement_date   = [self.fake.date_between_dates(
                                    date_start=datetime.date(2000, 1, 1),
                                    date_end=datetime.date(2023, 4, 30))for _ in range(self.num_records_mov)]
            )

        return \
            {
                'associate': self.dict_associate,
                'account': self.dict_account,
                'card': self.dict_card,
                'movement': self.dict_movement
             }


class FakeDataTransf(FakeData):
    """
        FakeDataTransf is a class that extends the FakeData class to generate and transform
        fake data for associates, accounts, cards, and movements. It provides methods to
        assign random data to these entities and return them as Polars DataFrames.

            tb_associate (dict): A dictionary containing associate data.
            tb_account (dict): A dictionary containing account data.
            tb_card (dict): A dictionary containing card data.
            tb_movement (dict): A dictionary containing movement data.
            num_records_mov (int): The number of records in the movement table.

        Methods:
            __init__(self, country: str = 'en_US') -> None:
                Initializes the FakeDataTransf class with the specified country.

            transf_account(self) -> None:
            transf_card(self) -> None:
            transf_movement(self) -> dict[str, list]:
            data_dict(self) -> tuple[str, pl.DataFrame]:
    """

    def __init__(self, country:str = 'en_US') -> None:
        super().__init__(country)
        self.tb_associate = self.default_base().get('associate')
        self.tb_account = self.default_base().get('account')
        self.tb_card = self.default_base().get('card')
        self.tb_movement = self.default_base().get('movement')


    def transf_account(self) -> None:
        """
            Assigns a random associate ID to each account record.

            This method retrieves a list of associate IDs from the 'tb_associate' table
            and assigns a randomly chosen associate ID to each account record in the
            'tb_account' table. The number of account records is determined by the
            'num_records_act' attribute.

            Returns:
                None
        """

        list_associate_id = self.tb_associate.get('associate_id')
        self.tb_account['fk_associate_id'] = [random.choice(list_associate_id) for _ in range(self.num_records_act)]


    def transf_card(self) -> None:
        """
            Generates and assigns fake card data to the `tb_card` attribute.

            This method creates a list of card names by combining random first and last names
            from the `tb_associate` attribute. It also generates lists of account IDs and
            associate IDs by randomly selecting from the `tb_account` attribute. These lists
            are then assigned to the `tb_card` attribute.

            Attributes:
                tb_associate (dict): A dictionary containing 'name' and 'last_name' keys with lists of names.
                tb_account (dict): A dictionary containing 'account_id' and 'fk_associate_id' keys with lists of IDs.
                tb_card (dict): A dictionary to which the generated card data will be assigned.
                num_records_ass (int): The number of records in the associate table.
                num_records_card (int): The number of records to generate for the card table.
                num_records_act (int): The number of records in the account table.
                fake (Faker): An instance of the Faker library used to generate random data.

            Returns:
                None
        """

        list_account_id   = list()
        list_associate_id = list()

        name = self.tb_associate.get('name')
        last_name = self.tb_associate.get('last_name')
        account_id = self.tb_account.get('account_id')
        associate_id = self.tb_account.get('fk_associate_id')

        full_name = [f'{name[_]} {last_name[_]}' for _ in range(self.num_records_ass)]
        card_name = [random.choice(full_name) for _ in range(self.num_records_card)]


        for _ in range(self.num_records_card):
            number = self.fake.random_int(min=0, max=self.num_records_act-1)
            list_account_id.append(account_id[number])
            list_associate_id.append(associate_id[number])

        self.tb_card['card_name'] = card_name
        self.tb_card['fk_account_id'] = list_account_id
        self.tb_card['fk_associate_id'] = list_associate_id


    def transf_movement(self) -> dict[str, list]:
        """
            Generates a dictionary with transformed movement data.

            This method selects a random card ID from the list of card IDs in the `tb_card` table
            and assigns it to the `card_id` field in the `tb_movement` table for a specified number
            of records.

            Returns:
                dict[str, list]: A dictionary where the key is a string representing the field name
                                and the value is a list of values for that field.
        """

        card_list = self.tb_card.get('card_id')
        card_list_id = [random.choice(card_list) for _ in range(self.num_records_mov)]
        self.tb_movement['card_id'] = card_list_id


    def data_dict(self) -> tuple[str, pl.DataFrame]:
        """
            Generates a dictionary of data tables as Polars DataFrames.

            This method transforms the account, card, and movement data, and then
            returns a dictionary where the keys are the table names and the values
            are the corresponding Polars DataFrames.

            Returns:
                tuple[str, pl.DataFrame]: A dictionary with the following structure:
                        "conta": pl.DataFrame(self.tb_account),
        """

        self.transf_account()
        self.transf_card()
        self.transf_movement()

        return \
            {
                "associado": pl.DataFrame(self.tb_associate),
                "conta":  pl.DataFrame(self.tb_account),
                "cartao": pl.DataFrame(self.tb_card),
                "movimento": pl.DataFrame(self.tb_movement)
            }


if __name__ == "__main__":
    test = FakeDataTransf()
    print(test.data_dict())
