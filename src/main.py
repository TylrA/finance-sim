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

# todo: create a list of functions (events) that will be called (happen) once every time period according to the granularity.
# an "event" will possibly append a state to the FinanceHistory object (more/less cash, etc.)
FinanceEvent = Callable[[FinanceState, int, float], FinanceState]
financeEvents: list[FinanceEvent] = []

def constantSalariedIncome(salary: float) -> FinanceEvent:
    def incomeEvent(state: FinanceState, period: int, yearFraction: float):
        result = state.copy()
        result.cash += salary * yearFraction
        return result
    return incomeEvent

def constantExpense(yearlyExpense: float) -> FinanceEvent:
    def expenseEvent(state: FinanceState, period: int, yearFraction: float):
        result = state.copy()
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
        newState = financeData.data[-1]
        for funct in financeEvents:
            newState = funct(financeData.data[-1], eventIdx, float(granularity))
            financeData.appendEvent(newState)
