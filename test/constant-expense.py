import pytest
from finance_sim import *


def testExpenseMonthly():
    financeData = FinanceHistory(FinanceState(10000))
    financeData.setEventComponents([constantExpense(120)])
    financeData.passEvent(1, 1 / 12)
    financeData.passEvent(2, 1 / 12)
    assert financeData.data[0].cash == pytest.approx(10000)
    assert financeData.data[1].cash == pytest.approx(9990)
    assert financeData.data[2].cash == pytest.approx(9980)

def testExpenseAnnual():
    financeData = FinanceHistory(FinanceState(10000))
    financeData.setEventComponents([constantExpense(120)])
    financeData.passEvent(1, 1)
    financeData.passEvent(2, 1)
    assert financeData.data[0].cash == pytest.approx(10000)
    assert financeData.data[1].cash == pytest.approx(9880)
    assert financeData.data[2].cash == pytest.approx(9760)

def testExpenseZero():
    financeData = FinanceHistory(FinanceState(10000))
    financeData.setEventComponents([constantExpense(0)])
    financeData.passEvent(1, 1)
    financeData.passEvent(2, 1)
    assert financeData.data[0].cash == pytest.approx(10000)
    assert financeData.data[1].cash == pytest.approx(10000)
    assert financeData.data[2].cash == pytest.approx(10000)

