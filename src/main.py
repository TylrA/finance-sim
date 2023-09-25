from __future__ import annotations

from typing import Callable
import sys

class ConstantGrowthAsset(object):
    '''
    "Constant" really means constant exponential rate
    '''
    value: float
    appreciation: float
    
    def __init__(self, initialValue: float = 0, annualAppreciation: float = 0):
        self.value = initialValue
        self.appreciation = annualAppreciation

    def appreciate(self, yearFraction: float) -> ConstantGrowthAsset:
        value = self.value * (1 + self.appreciation) ** yearFraction
        return ConstantGrowthAsset(value, self.appreciation)

class FinanceState(object):
    def __init__(self, cash: float = 0):
        self.cash: float = cash
        self.constantGrowthAssets: list[ConstantGrowthAsset] = []

    def copy(self):
        result = FinanceState()
        result.cash = self.cash
        result.constantGrowthAssets = self.constantGrowthAssets
        return result


class FinanceHistory(object):
    def __init__(self, event: FinanceState):
        self.data: list[FinanceState] = []
        if not FinanceState is None:
            self.data.append(event)
    
    def appendEvent(self, event: FinanceState):
        self.data.append(event)

FinanceEvent = Callable[[FinanceHistory, FinanceState, int, float], FinanceState]
financeEvents: list[FinanceEvent] = []

def constantSalariedIncome(salary: float) -> FinanceEvent:
    def incomeEvent(history: FinanceHistory, state: FinanceState, period: int, yearFraction: float):
        result = state.copy()
        result.cash += salary * yearFraction
        return result
    return incomeEvent

def constantExpense(yearlyExpense: float) -> FinanceEvent:
    def expenseEvent(history: FinanceHistory, state: FinanceState, period: int, yearFraction: float):
        result = state.copy()
        result.cash -= yearlyExpense * yearFraction
        return result
    return expenseEvent

def appreciateConstantAssets(history: FinanceHistory, state: FinanceState, period: int, yearFraction: float) -> FinanceState:
    result = state.copy()
    result.constantGrowthAssets = [asset.appreciate(yearFraction) for asset in
                                   result.constantGrowthAssets]
    return result

if __name__ == '__main__':
    if len(sys.argv) <= 2:
        print("Usage: {} <granularity> <time-period>".format(sys.argv[0]))
        print()
        print("   granularity  number of events in a year (e.g. 12 for monthly)")
        print("   time-period  number of years to calculate")
        exit(1)

    granularity = sys.argv[1]
    timePeriod = sys.argv[2]

    if not granularity.isnumeric():
        print("granularity must be numeric, got {}".format(granularity))
        exit(1)
    if not timePeriod.isnumeric():
        print("time-period must be numeric, got {}".format(timePeriod))
        exit(1)

    financeData = FinanceHistory(FinanceState(0))
    initialData = FinanceState(100)
    initialData.constantGrowthAssets.append(ConstantGrowthAsset(10000, 0.05))
    financeEvents.append(constantSalariedIncome(50000))
    financeEvents.append(constantExpense(20000))
    financeEvents.append(appreciateConstantAssets)
    financeData.data[0] = initialData

    for eventIdx in range(int(granularity) * int(timePeriod)):
        newState = financeData.data[eventIdx]
        for funct in financeEvents:
            newState = funct(financeData, newState, eventIdx, 1 / float(granularity))
        financeData.appendEvent(newState)

    # temp report for testing
    print("{}{}{}".format("INDEX".ljust(8), "CASH".ljust(15), "INVESTMENT"))
    for idx in range(len(financeData.data)):
        print("{}{}{}".format(str(idx).ljust(8),
                              str(financeData.data[idx].cash).ljust(15),
                              str(financeData.data[idx].constantGrowthAssets[0].value)))
