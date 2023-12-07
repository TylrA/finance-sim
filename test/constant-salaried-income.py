import pytest
from finance_sim import *
from calendar import monthrange
from datetime import date
from dateutil.relativedelta import relativedelta

def testSalariedIncomeMonthly():
    eventGroup = EventGroup(date(2000, 1, 1),
                            { 'i': ConstantSalariedIncome('i',
                                                          120,
                                                          AccrualModel.PeriodicMonthly),
                              'cash': CashEvent('cash', 0) })
    financeData = FinanceHistory(eventGroup)
    previousCash = financeData.latestEvents().events['cash'].value
    delta = relativedelta(months=1)
    for month in range(2, 100):
        financeData.passEvent(date(2000 + (month) // 12, ((month - 1) % 12) + 1, 1), delta)
        newCash = financeData.latestEvents().events['cash'].value
        assert newCash == pytest.approx(previousCash + 10)
        previousCash = newCash
    
def testSalariedIncomeSemiMonthly():
    eventGroup = EventGroup(date(2000, 1, 15),
                            { 'i': ConstantSalariedIncome('i',
                                                          120,
                                                          AccrualModel.PeriodicSemiMonthly),
                              'cash': CashEvent('cash', 0) })
    financeData = FinanceHistory(eventGroup)
    previousCash = financeData.latestEvents().events['cash'].value
    delta = relativedelta(months=1)
    for idx in range(1, 100):
        month = (idx // 2) % 12 + 1
        year = 2000 + (month // 12)
        day = monthrange(year, month)[1] if idx % 2 else 15
        adjustedDate = date(year, month, day)
        if idx % 2:
            delta = relativedelta(days = day - 15)
        else:
            delta = relativedelta(days = 15)
        financeData.passEvent(adjustedDate, delta)
        newCash = financeData.latestEvents().events['cash'].value
        assert newCash == pytest.approx(previousCash + 5)
        previousCash = newCash
    
def testSalariedIncomeSemiAnnual():
    eventGroup = EventGroup(date(1999, 6, 1),
                            { 'i': ConstantSalariedIncome('i',
                                                          100,
                                                          AccrualModel.PeriodicMonthly),
                              'cash': CashEvent('cash', 0) })
    financeData = FinanceHistory(eventGroup)
    previousCash = financeData.latestEvents().events['cash'].value
    for year in range(2000, 2006):
        for month in [1, 6]:
            financeData.passEvent(date(year, month, 1), relativedelta(months=6))
            newCash = financeData.latestEvents().events['cash'].value
            assert newCash == pytest.approx(previousCash + 50)
            previousCash = newCash

def testSalariedIncomeBiAnnual():
    eventGroup = EventGroup(date(1999, 1, 1),
                            { 'i': ConstantSalariedIncome('i',
                                                          100,
                                                          AccrualModel.PeriodicYearly),
                              'cash': CashEvent('cash', 0) })
    financeData = FinanceHistory(eventGroup)
    previousCash = financeData.latestEvents().events['cash'].value
    for year in range(2000, 2009, 2):
        financeData.passEvent(date(year, 1, 1), relativedelta(years=2))
        newCash = financeData.latestEvents().events['cash'].value
        assert newCash == pytest.approx(previousCash + 200)
        previousCash = newCash

def testSalariedIncomeZero():
    eventGroup = EventGroup(date(1999, 12, 1),
                            { 'i': ConstantSalariedIncome('i',
                                                          0,
                                                          AccrualModel.PeriodicMonthly),
                              'cash': CashEvent('cash', 0) })
    financeData = FinanceHistory(eventGroup)
    for month in range(1, 13):
        financeData.passEvent(date(2000, month, 1), relativedelta(months=1))
        newCash = financeData.latestEvents().events['cash'].value
        assert newCash == 0

