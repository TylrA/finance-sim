from __future__ import annotations

from typing import Callable
from dataclasses import dataclass
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

class AmortizingLoan(object):
    def __init__(self,
                 name: str,
                 initialPrinciple: float = 0,
                 loanAmount: float = 0,
                 rate: float = 0.05,
                 remainingTermInYears: float = 20
                 ):
        self.name = name
        self.principle = initialPrinciple
        self.loanAmount = loanAmount
        self.rate = rate
        self.term = remainingTermInYears

    def copy(self):
        result = AmortizingLoan(self.name, self.principle, self.loanAmount, self.rate, self.term)
        return result
        

class FinanceState(object):
    def __init__(self, cash: float = 0):
        self.cash: float = cash
        self.constantGrowthAssets: list[ConstantGrowthAsset] = []
        self.amortizingLoans: dict[str, AmortizingLoan] = {}
        self.taxableIncome: float = 0
        self.taxesPaid: float = 0

    def copy(self):
        result = FinanceState()
        result.cash = self.cash
        result.constantGrowthAssets = self.constantGrowthAssets
        result.amortizingLoans = self.amortizingLoans
        result.taxableIncome = self.taxableIncome
        return result

class FinanceHistory(object):
    def __init__(self, event: FinanceState):
        self.data: list[FinanceState] = [event]

    def setEventComponents(self, events: list[FinanceEvent]):
        self.events = events

    def passEvent(self, idx: int, yearFraction: float):
        newState = self.data[idx - 1].copy()
        for event in self.events:
            newState = event(self, newState, idx, yearFraction)
        self.data.append(newState)
    
    def appendEvent(self, event: FinanceState):
        self.data.append(event)

    def latestEvent(self):
        return self.data[-1]


FinanceEvent = Callable[[FinanceHistory, FinanceState, int, float], FinanceState]


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

def makeAmortizedPayments(history: FinanceHistory, state: FinanceState, period: int, yearFraction: float) -> FinanceState:
    result = state.copy()
    for name, amortizingLoan in result.amortizingLoans.items():
        newLoan = amortizingLoan.copy()
        i = (1 + newLoan.rate) ** yearFraction - 1
        numerator = (newLoan.loanAmount - newLoan.principle) * i
        denominator = 1 - (1 + i) ** -(newLoan.term / yearFraction)
        paymentAmount = numerator / denominator
        newLoan.principle += paymentAmount - (newLoan.loanAmount - newLoan.principle) * \
            newLoan.rate * yearFraction
        newLoan.term -= yearFraction
        result.cash -= paymentAmount
        result.amortizingLoans[name] = newLoan
    return result

@dataclass
class TaxBracket(object):
    rate: float
    income: float

def taxPaymentSchedule(frequency: float, brackets: list[TaxBracket]) -> FinanceEvent:
    if brackets[0].income != 0.0:
        raise RuntimeError('brackets must start with a zero income bracket')

    def payTaxes(history: FinanceHistory, state: FinanceState, period: int, yearFraction: float) -> FinanceState:
        result = state.copy()
        if ((period * yearFraction) % frequency) < yearFraction:
            taxDue = 0
            for bracket in brackets[::-1]:
                adjustedIncome = bracket.income * yearFraction
                if result.taxableIncome > adjustedIncome:
                    marginAboveBracket = result.taxableIncome - adjustedIncome
                    taxDue += bracket.rate * marginAboveBracket
                    result.taxableIncome -= marginAboveBracket
            result.cash -= taxDue
            result.taxesPaid += taxDue
        return result

    return payTaxes

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

    initialData = FinanceState(100)
    financeEvents: list[FinanceEvent] = []
    initialData.constantGrowthAssets.append(ConstantGrowthAsset(10000, 0.05))
    financeEvents.append(constantSalariedIncome(50000))
    financeEvents.append(constantExpense(20000))
    financeEvents.append(appreciateConstantAssets)
    financeData = FinanceHistory(initialData)
    financeData.setEventComponents(financeEvents)

    for eventIdx in range(int(granularity) * int(timePeriod)):
        financeData.passEvent(eventIdx, 1 / float(granularity))

    # temp report for testing
    print("{}{}{}".format("INDEX".ljust(8), "CASH".ljust(15), "INVESTMENT"))
    for idx in range(len(financeData.data)):
        print("{}{}{}".format(str(idx).ljust(8),
                              str(financeData.data[idx].cash).ljust(15),
                              str(financeData.data[idx].constantGrowthAssets[0].value)))
