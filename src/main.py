from typing import Callable
import sys

class FinanceState(object):
    def __init__(self, cash: float = 0):
        self.cash = cash

    def copy(self):
        result = FinanceState(self.cash)
        return result


class FinanceHistory(object):
    def __init__(self, event: FinanceState):
        self.data: list[FinanceState] = []
        if not FinanceState is None:
            self.data.append(event)
    
    def appendEvent(self, event: FinanceState):
        self.data.append(event)

FinanceEvent = Callable[[FinanceHistory, int, float], FinanceState]
financeEvents: list[FinanceEvent] = []

def constantSalariedIncome(salary: float) -> FinanceEvent:
    def incomeEvent(history: FinanceHistory, period: int, yearFraction: float):
        result = history.data[0].copy()
        result.cash += salary * yearFraction
        return result
    return incomeEvent

def constantExpense(yearlyExpense: float) -> FinanceEvent:
    def expenseEvent(history: FinanceHistory, period: int, yearFraction: float):
        result = history.data[0].copy()
        result.cash -= yearlyExpense * yearFraction
        return result
    return expenseEvent

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

    for eventIdx in range(int(granularity) * int(timePeriod)):
        for funct in financeEvents:
            newState = funct(financeData, eventIdx, float(granularity))
            financeData.appendEvent(newState)
