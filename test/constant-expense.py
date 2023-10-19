import pytest
from finance_sim import *
from datetime import date
from dateutil.relativedelta import relativedelta


def testExpenseMonthly():
    initialState = FinanceState(date(1999, 12, 1))
    initialState.cash = 10000
    financeData = FinanceHistory(initialState)
    financeData.setEventComponents([constantExpense(120, AccrualModel.PeriodicMonthly)])
    delta = relativedelta(months=1)
    financeData.passEvent(date(2000, 1, 1), delta)
    financeData.passEvent(date(2000, 2, 1), delta)
    assert financeData.data[0].cash == pytest.approx(10000)
    assert financeData.data[1].cash == pytest.approx(9990)
    assert financeData.data[2].cash == pytest.approx(9980)

def testExpenseAnnual():
    initialState = FinanceState(date(2001, 1, 1))
    initialState.cash = 10000
    financeData = FinanceHistory(initialState)
    financeData.setEventComponents([constantExpense(120, AccrualModel.ProRata)])
    delta = relativedelta(years=1)
    financeData.passEvent(date(2002, 1, 1), delta)
    financeData.passEvent(date(2003, 1, 1), delta)
    assert financeData.data[0].cash == pytest.approx(10000)
    assert financeData.data[1].cash == pytest.approx(9880)
    assert financeData.data[2].cash == pytest.approx(9760)

def testExpenseZero():
    initialState = FinanceState(date(2001, 1, 1))
    initialState.cash = 10000
    financeData = FinanceHistory(initialState)
    financeData.setEventComponents([constantExpense(0, AccrualModel.ProRata)])
    delta = relativedelta(years=1)
    financeData.passEvent(date(2002, 1, 1), delta)
    financeData.passEvent(date(2003, 1, 1), delta)
    assert financeData.data[0].cash == pytest.approx(10000)
    assert financeData.data[1].cash == pytest.approx(10000)
    assert financeData.data[2].cash == pytest.approx(10000)

