import pytest
from finance_sim import *
from datetime import date
from dateutil.relativedelta import relativedelta

def testConstantGrowthMonthly():
    eventGroup = EventGroup(date(1999, 12, 1),
                            { 'g': ConstantGrowthAsset(None,
                                                       'g',
                                                       AccrualModel.PeriodicMonthly,
                                                       100,
                                                       0.5),
                              'cash': CashEvent(None, 'cash', 0) })
    financeData = FinanceHistory(eventGroup)
    monthlyInterest = 1.5 ** (1 / 12)
    delta = relativedelta(months=1)
    for month in range(1, 10):
        financeData.passEvent(date(2000, month, 1), delta)
        event = financeData.data[month].events['g']
        assert financeData.data[month].events['g'].value == \
            pytest.approx(financeData.data[month-1].events['g'].value * monthlyInterest)

def testConstantGrowthAnnually():
    eventGroup = EventGroup(date(2001, 1, 1),
                            { 'g': ConstantGrowthAsset(None,
                                                       'g',
                                                       AccrualModel.PeriodicYearly,
                                                       100,
                                                       0.5),
                              'cash': CashEvent(None, 'cash', 0) })
    financeData = FinanceHistory(eventGroup)
    delta = relativedelta(years=1)
    for year, idx in zip(range(2002, 2010), range(1, 9)):
        financeData.passEvent(date(year, 1, 1), delta)
        assert financeData.data[idx].events['g'].value == \
            pytest.approx(financeData.data[idx-1].events['g'].value * 1.5)

