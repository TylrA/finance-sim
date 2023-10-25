import pytest
from finance_sim import *
from datetime import date
from dateutil.relativedelta import relativedelta

def testConstantGrowthMonthly():
    initialState = FinanceState(date(1999, 12, 1))
    initialState.constantGrowthAssets.append(
        ConstantGrowthAsset(AccrualModel.PeriodicMonthly, 100, 0.5))
    financeData = FinanceHistory(initialState)
    financeData.setEventComponents([appreciateConstantAssets])
    monthlyInterest = 1.5 ** (1 / 12)
    delta = relativedelta(months=1)
    for month in range(1, 10):
        financeData.passEvent(date(2000, month, 1), delta)
        assert financeData.data[month].constantGrowthAssets[0].value == \
            pytest.approx(
                financeData.data[month-1].constantGrowthAssets[0].value * monthlyInterest)

def testConstantGrowthAnnually():
    initialState = FinanceState(date(2001, 1, 1))
    initialState.constantGrowthAssets.append(
        ConstantGrowthAsset(AccrualModel.PeriodicYearly, 100, 0.5))
    financeData = FinanceHistory(initialState)
    financeData.setEventComponents([appreciateConstantAssets])
    delta = relativedelta(years=1)
    for year, idx in zip(range(2002, 2010), range(1, 9)):
        financeData.passEvent(date(year, 1, 1), delta)
        assert financeData.data[idx].constantGrowthAssets[0].value == \
            pytest.approx(financeData.data[idx-1].constantGrowthAssets[0].value * 1.5)

