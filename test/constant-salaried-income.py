import pytest
from finance_sim import *

def testSalariedIncomeMonthly():
    financeData = FinanceHistory(FinanceState(0))
    events: list[FinanceEvent] = [constantSalariedIncome(120)]
    financeData.setEventComponents(events)
    previousCash = financeData.data[0].cash
    for idx in range(1, 100):
        financeData.passEvent(idx, 1 / 12)
        newCash = financeData.data[idx].cash
        assert newCash == pytest.approx(previousCash + 10)
        previousCash = newCash
    
def testSalariedIncomeBiMonthly():
    financeData = FinanceHistory(FinanceState(0))
    events: list[FinanceEvent] = [constantSalariedIncome(120)]
    financeData.setEventComponents(events)
    previousCash = financeData.data[0].cash
    for idx in range(1, 100):
        financeData.passEvent(idx, 1 / 24)
        newCash = financeData.data[idx].cash
        assert newCash == pytest.approx(previousCash + 5)
        previousCash = newCash
    
def testSalariedIncomeBiAnnual():
    financeData = FinanceHistory(FinanceState(0))
    events: list[FinanceEvent] = [constantSalariedIncome(100)]
    financeData.setEventComponents(events)
    previousCash = financeData.data[0].cash
    for idx in range(1, 10):
        financeData.passEvent(idx, 2)
        newCash = financeData.data[idx].cash
        assert newCash == pytest.approx(previousCash + 200)
        previousCash = newCash

def testSalariedIncomeZero():
    financeData = FinanceHistory(FinanceState(0))
    events: list[FinanceEvent] = [constantSalariedIncome(0)]
    financeData.setEventComponents(events)
    for idx in range(1, 10):
        financeData.passEvent(idx, 2)
        newCash = financeData.data[idx].cash
        assert newCash == 0

