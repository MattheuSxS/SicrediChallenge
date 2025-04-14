import pytest
import datetime
import polars as pl
from src.modules.fake_data import FakeData
from src.modules.fake_data import FakeDataTransf


@pytest.fixture
def fake_data_instance():
    """Fixture to create an instance of FakeData."""
    return FakeData()


def test_default_base_structure(fake_data_instance):
    """Test if the default_base method returns a dictionary with the correct structure."""
    base_data = fake_data_instance.default_base()

    assert isinstance(base_data, dict)
    assert set(base_data.keys()) == {'associate', 'account', 'card', 'movement'}

    # Check structure of 'associate'
    associate = base_data['associate']
    assert set(associate.keys()) == {'associate_id', 'name', 'last_name', 'age', 'email'}
    assert len(associate['associate_id']) == fake_data_instance.num_records_ass

    # Check structure of 'account'
    account = base_data['account']
    assert set(account.keys()) == {'account_id', 'account_type', 'creation_date'}
    assert len(account['account_id']) == fake_data_instance.num_records_act

    # Check structure of 'card'
    card = base_data['card']
    assert set(card.keys()) == {'card_id', 'card_number'}
    assert len(card['card_id']) == fake_data_instance.num_records_card

    # Check structure of 'movement'
    movement = base_data['movement']
    assert set(movement.keys()) == {'movement_id', 'vlr_transaction', 'des_transaction', 'movement_date'}
    assert len(movement['movement_id']) == fake_data_instance.num_records_mov


def test_associate_data(fake_data_instance):
    """Test the data generated for associates."""
    associate = fake_data_instance.default_base()['associate']

    assert all(isinstance(id, int) for id in associate['associate_id'])
    assert all(isinstance(name, str) for name in associate['name'])
    assert all(isinstance(last_name, str) for last_name in associate['last_name'])
    assert all(18 <= age <= 100 for age in associate['age'])
    assert all('@' in email for email in associate['email'])


def test_account_data(fake_data_instance):
    """Test the data generated for accounts."""
    account = fake_data_instance.default_base()['account']

    assert all(isinstance(id, int) for id in account['account_id'])
    assert all(account_type in ['Corrente', 'Poupanca', 'Personnalite'] for account_type in account['account_type'])
    assert all(isinstance(date, datetime.date) for date in account['creation_date'])


def test_card_data(fake_data_instance):
    """Test the data generated for cards."""
    card = fake_data_instance.default_base()['card']

    assert all(isinstance(id, int) for id in card['card_id'])
    assert all(isinstance(number, int) for number in card['card_number'])


def test_movement_data(fake_data_instance):
    """Test the data generated for movements."""
    movement = fake_data_instance.default_base()['movement']

    assert all(isinstance(id, int) for id in movement['movement_id'])
    assert all(isinstance(value, float) for value in movement['vlr_transaction'])
    assert all(description in ['debit', 'credit'] for description in movement['des_transaction'])
    assert all(isinstance(date, datetime.date) for date in movement['movement_date'])


@pytest.fixture
def fake_data_transf_instance():
    """Fixture to create an instance of FakeDataTransf."""
    return FakeDataTransf()


def test_transf_account(fake_data_transf_instance):
    """Test the transf_account method."""
    fake_data_transf_instance.transf_account()
    account_data = fake_data_transf_instance.tb_account

    assert 'fk_associate_id' in account_data
    assert len(account_data['fk_associate_id']) == fake_data_transf_instance.num_records_act
    assert all(associate_id in fake_data_transf_instance.tb_associate['associate_id'] for associate_id in account_data['fk_associate_id'])


def test_transf_card(fake_data_transf_instance):
    """Test the transf_card method."""
    fake_data_transf_instance.transf_account()
    fake_data_transf_instance.transf_card()
    card_data = fake_data_transf_instance.tb_card

    assert 'card_name' in card_data
    assert 'fk_account_id' in card_data
    assert 'fk_associate_id' in card_data
    assert len(card_data['card_name']) == fake_data_transf_instance.num_records_card
    assert len(card_data['fk_account_id']) == fake_data_transf_instance.num_records_card
    assert len(card_data['fk_associate_id']) == fake_data_transf_instance.num_records_card
    assert all(account_id in fake_data_transf_instance.tb_account['account_id'] for account_id in card_data['fk_account_id'])
    assert all(associate_id in fake_data_transf_instance.tb_account['fk_associate_id'] for associate_id in card_data['fk_associate_id'])


def test_transf_movement(fake_data_transf_instance):
    """Test the transf_movement method."""
    fake_data_transf_instance.transf_account()
    fake_data_transf_instance.transf_card()
    fake_data_transf_instance.transf_movement()
    movement_data = fake_data_transf_instance.tb_movement

    assert 'card_id' in movement_data
    assert len(movement_data['card_id']) == fake_data_transf_instance.num_records_mov
    assert all(card_id in fake_data_transf_instance.tb_card['card_id'] for card_id in movement_data['card_id'])


def test_data_dict(fake_data_transf_instance):
    """Test the data_dict method."""
    data_dict = fake_data_transf_instance.data_dict()

    assert isinstance(data_dict, dict)
    assert set(data_dict.keys()) == {'associado', 'conta', 'cartao', 'movimento'}

    # Check if all values are Polars DataFrames
    assert all(isinstance(df, pl.DataFrame) for df in data_dict.values())

    # Check the structure of each DataFrame
    associado_df = data_dict['associado']
    conta_df = data_dict['conta']
    cartao_df = data_dict['cartao']
    movimento_df = data_dict['movimento']

    assert set(associado_df.columns) == {'associate_id', 'name', 'last_name', 'age', 'email'}
    assert set(conta_df.columns) == {'account_id', 'account_type', 'creation_date', 'fk_associate_id'}
    assert set(cartao_df.columns) == {'card_id', 'card_number', 'card_name', 'fk_account_id', 'fk_associate_id'}
    assert set(movimento_df.columns) == {'movement_id', 'vlr_transaction', 'des_transaction', 'movement_date', 'card_id'}
