import pytest
from finance_sim import *
from datetime import date
from dateutil.relativedelta import relativedelta

def testParseConfigTime():
    path = 'examples/finance-config.yaml'
    config = parseConfig(path)
    assert config.time.accrualModel == AccrualModel.PeriodicMonthly
    assert config.time.granularity == relativedelta(months=1)
    assert config.time.period == 30
    assert config.time.startingDate == date(2000, 1, 1)

def testParseConfigInitialState():
    path = 'examples/finance-config.yaml'
    config = parseConfig(path)
    assert len(config.initialState) == 2
    assert config.initialState[0].type == StateType.cash
    assert config.initialState[0].name == "Savings"
    assert config.initialState[0].value == 100
    assert config.initialState[1].type == StateType.constantGrowthAsset
    assert config.initialState[1].name == "CD Savings"
    assert config.initialState[1].value == 500
    # todo: add appreciation
