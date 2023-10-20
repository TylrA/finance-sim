import pytest
from finance_sim import *
from datetime import date
from dateutil.relativedelta import relativedelta

def testSalariedIncomeMonthly():
    financeData = FinanceHistory(FinanceState(date(2000, 1, 1)))
    events = [constantSalariedIncome(120, AccrualModel.PeriodicMonthly)]
    financeData.setEventComponents(events)
    previousCash = financeData.data[0].cash
    delta = relativedelta(months=1)
    for month in range(2, 100):
        financeData.passEvent(date(2000 + (month) // 12, ((month - 1) % 12) + 1, 1), delta)
        newCash = financeData.data[idx].cash
        assert newCash == pytest.approx(previousCash + 10)
        previousCash = newCash
    
def testSalariedIncomeSemiMonthly():
    financeData = FinanceHistory(FinanceState(date(2000, 1, 1)))
    events: list[FinanceEvent] = [constantSalariedIncome(120, AccrualModel.ProRata)]
    financeData.setEventComponents(events)
    previousCash = financeData.data[0].cash
    delta = relativedelta(months=1)
    for idx in range(1, 100):
        month = idx // 2 + 1
        day = 15 if month % 2 else 1
        adjustedDate = date(2000 + (month // 12), month, day)
        if month % 2:
            delta = relativedelta(days=14)
        else:
            delta = relativedelta(days=(int(((date(2000 + (month // 12), month, 1) \
                                              + relativedelta(months=1)) - adjustedDate)
                                            .total_seconds()) // (24 * 3600)))
        financeData.passEvent(adjustedDate, delta)
        newCash = financeData.data[idx].cash
        assert newCash == pytest.approx(previousCash + 5)
        previousCash = newCash
    
def testSalariedIncomeBiAnnual():
    financeData = FinanceHistory(FinanceState(date(1999, 6, 1)))
    events: list[FinanceEvent] = [constantSalariedIncome(100, AccrualModel.ProRata)]
    financeData.setEventComponents(events)
    previousCash = financeData.data[0].cash
    for year in range(2000, 2006):
        for month in [1, 6]:
            financeData.passEvent(date(year, month, 1), relativedelta(months=6))
            newCash = financeData.data[idx].cash
            assert newCash == pytest.approx(previousCash + 200)
            previousCash = newCash

def testSalariedIncomeZero():
    financeData = FinanceHistory(FinanceState(date(1999, 12, 1)))
    events: list[FinanceEvent] = [constantSalariedIncome(0, AccrualModel.PeriodicMonthly)]
    financeData.setEventComponents(events)
    for month in range(1, 13):
        financeData.passEvent(date(2000, month, 1), relativedelta(months=1))
        newCash = financeData.data[idx].cash
        assert newCash == 0

