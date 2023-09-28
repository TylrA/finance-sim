import pytest
from finance_sim import *

def testConstantGrowthMonthly():
    initialState = FinanceState()
    initialState.constantGrowthAssets.append(ConstantGrowthAsset(100, 0.5))
    financeData = FinanceHistory(initialState)
    financeData.setEventComponents([appreciateConstantAssets])
    monthlyInterest = 1.5 ** (1 / 12)
    for i in range(1, 10):
        financeData.passEvent(i, 1 / 12)
        assert financeData.data[i].constantGrowthAssets[0].value == \
            pytest.approx(financeData.data[i-1].constantGrowthAssets[0].value * monthlyInterest)

def testConstantGrowthAnnually():
    initialState = FinanceState()
    initialState.constantGrowthAssets.append(ConstantGrowthAsset(100, 0.5))
    financeData = FinanceHistory(initialState)
    financeData.setEventComponents([appreciateConstantAssets])
    for i in range(1, 10):
        financeData.passEvent(i, 1)
        assert financeData.data[i].constantGrowthAssets[0].value == \
            pytest.approx(financeData.data[i-1].constantGrowthAssets[0].value * 1.5)

