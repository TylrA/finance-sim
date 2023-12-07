from __future__ import annotations
from ctypes import ArgumentError

import sys
import abc

from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta
from math import pow
from typing import Callable, Optional

from .scheduling import AccrualModel, portionOfYear

class AbstractEvent(abc.ABC):
    '''
    "FinanceEvent" is a good name, but that's already taken. This should deprecate/rebase
    a lot of FinanceState and FinanceEvent. They can keep their names in the meantime.
    '''
    name: str

    @abc.abstractmethod
    def transform(self,
                  history: FinanceHistory,
                  date: date,
                  delta: relativedelta) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def copy(self) -> AbstractEvent:
        raise NotImplementedError()

class EventGroup(object):
    date: date
    events: dict[str, AbstractEvent]
    def __init__(self, date: date, events: dict[str, AbstractEvent]):
        self.date = date
        self.events = events

    def copy(self):
        return EventGroup(self.date,
                          { name: event.copy() for name, event in self.events.items() })

class CashEvent(AbstractEvent):
    value: float
    def __init__(self, name: str, value: float):
        self.name = name
        self.value = value

    def transform(self,
                  history: FinanceHistory,
                  date: date,
                  delta: relativedelta):
        pass

    def copy(self):
        return CashEvent(self.name, self.value)

@dataclass
class TaxBracket(object):
    rate: float
    income: float

class TaxPaymentEvent(AbstractEvent):
    frequency: relativedelta
    accrualModel: AccrualModel
    brackets: list[TaxBracket]
    taxableIncome: float
    taxesPaid: float
    
    def __init__(self,
                 name: str,
                 frequency: relativedelta,
                 accrualModel: AccrualModel,
                 brackets: list[TaxBracket]):
        self.name = name
        self.frequency = frequency
        self.accrualModel = accrualModel
        self.brackets = brackets
        self.taxableIncome = 0
        self.taxesPaid = 0

    def transform(self, history: FinanceHistory, date: date, delta: relativedelta):
        if (date - delta) <= (date - self.frequency):
            taxDue = 0
            for bracket in self.brackets[::-1]:
                adjustedIncomeThreshold = bracket.income * \
                    portionOfYear(date, delta, self.accrualModel)
                if self.taxableIncome > adjustedIncomeThreshold:
                    marginAboveBracket = self.taxableIncome - adjustedIncomeThreshold
                    taxDue += bracket.rate * marginAboveBracket
                    self.taxableIncome -= marginAboveBracket
            addToCash(history.pendingEvent, -taxDue)
            self.taxesPaid += taxDue
                

    def copy(self):
        result = TaxPaymentEvent(self.name,
                                 self.frequency,
                                 self.accrualModel,
                                 self.brackets)
        result.taxableIncome = self.taxableIncome
        result.taxesPaid = self.taxesPaid
        return result

class ConstantGrowthAsset(AbstractEvent):
    '''
    "Constant" really means constant exponential rate
    '''
    value: float
    appreciation: float
    
    def __init__(self,
                 name: str,
                 accrualModel: AccrualModel,
                 initialValue: float = 0,
                 annualAppreciation: float = 0):
        self.name = name
        self.value = initialValue
        self.appreciation = annualAppreciation
        self.accrualModel = accrualModel

    def transform(self,
                  history: FinanceHistory,
                  date: date,
                  delta: relativedelta):
        portion = portionOfYear(date, delta, self.accrualModel)
        self.value *= pow(1 + self.appreciation, portion)

    def copy(self) -> ConstantGrowthAsset:
        result = ConstantGrowthAsset(self.name, self.accrualModel, self.value, self.appreciation)
        return result

    def __str__(self) -> str:
        return str(self.value)

def addToCash(events: EventGroup,
              difference: float,
              taxable: bool = True) -> None:
    if difference < 0:
        for _, event in events.events.items():
            if isinstance(event, CashEvent):
                if event.value >= -difference:
                    event.value += difference
                    difference = 0
                elif event.value > 0:
                    difference += event.value
                    event.value = 0
        if difference > 0:
            raise RuntimeError("not enough money to subtract")
    else:
        cashEvent: Optional[CashEvent] = None
        taxPaymentEvent: Optional[TaxPaymentEvent] = None
        for _, event in events.events.items():
            if isinstance(event, CashEvent):
                cashEvent = event
                if taxPaymentEvent:
                    break
            elif isinstance(event, TaxPaymentEvent):
                taxPaymentEvent = event
                if cashEvent:
                    break
        if cashEvent:
            cashEvent.value += difference
        if taxable and taxPaymentEvent:
            taxPaymentEvent.taxableIncome += difference

class AmortizingLoan(AbstractEvent):
    accrualModel: AccrualModel
    principle: float
    loanAmount: float
    rate: float
    term: float
    payment: float
    
    def __init__(self,
                 name: str,
                 accrualModel: AccrualModel,
                 initialPrinciple: float = 0,
                 loanAmount: float = 0,
                 rate: float = 0.05,
                 remainingTermInYears: float = 20,
                 payment: float = -1):
        self.name = name
        self.accrualModel = accrualModel
        self.principle = initialPrinciple
        self.loanAmount = loanAmount
        self.rate = rate
        self.term = remainingTermInYears
        self.payment = payment

    def transform(self,
                  history: FinanceHistory,
                  date: date,
                  period: relativedelta) -> None:
        yearFraction = portionOfYear(date, period, self.accrualModel)
        adjustedRate = pow(1 + self.rate, yearFraction) - 1
        interestPaid = (self.loanAmount - self.principle) * adjustedRate
        if self.payment < 0:
            denominator = 1 - pow(1 + adjustedRate, -(self.term / yearFraction))
            paymentAmount = interestPaid / denominator
            self.payment = paymentAmount
        self.principle += self.payment - interestPaid
        self.term -= yearFraction
        addToCash(history.pendingEvent, -self.payment)

    def copy(self):
        result = AmortizingLoan(self.name,
                                self.accrualModel,
                                self.principle,
                                self.loanAmount,
                                self.rate,
                                self.term,
                                self.payment)
        return result

class ConstantSalariedIncome(AbstractEvent):
    salary: float
    accrualModel: AccrualModel
    def __init__(self, name: str, salary: float, accrualModel: AccrualModel):
        self.name = name
        self.salary = salary
        self.accrualModel = accrualModel

    def transform(self,
                  history: FinanceHistory,
                  date: date,
                  period: relativedelta):
        portion = portionOfYear(date, period, self.accrualModel)
        addToCash(history.pendingEvent, portion * self.salary)

    def copy(self):
        return ConstantSalariedIncome(self.name, self.salary, self.accrualModel)

class ConstantExpense(AbstractEvent):
    yearlyExpense: float
    accrualModel: AccrualModel
    def __init__(self, name: str, yearlyExpense: float, accrualModel: AccrualModel):
        self.name = name
        self.yearlyExpense = yearlyExpense
        self.accrualModel = accrualModel

    def transform(self,
                  history: FinanceHistory,
                  date: date,
                  period: relativedelta):
        portion = portionOfYear(date, period, self.accrualModel)
        addToCash(history.pendingEvent, -portion * self.yearlyExpense)

    def copy(self):
        return ConstantExpense(self.name, self.yearlyExpense, self.accrualModel)

class FinanceState(object):
    def __init__(self, date: date = date.today()):
        self.date = date
        self.cash: float = 0
        self.constantGrowthAssets: list[ConstantGrowthAsset] = []
        self.amortizingLoans: dict[str, AmortizingLoan] = {}
        self.taxableIncome: float = 0
        self.taxesPaid: float = 0

    def copy(self):
        result = FinanceState()
        result.date = self.date
        result.cash = self.cash
        result.constantGrowthAssets = self.constantGrowthAssets
        result.amortizingLoans = self.amortizingLoans
        result.taxableIncome = self.taxableIncome
        result.taxesPaid = self.taxesPaid
        return result

class FinanceHistory(object):
    pendingEvent: EventGroup
    
    def __init__(self, event: EventGroup):
        self.data: list[EventGroup] = [event]
        self.events: list[FinanceEvent] = []

    def passEvent(self, date: date, period: relativedelta):
        self.pendingEvent = self.data[-1].copy()
        self.pendingEvent.date = date
        for _, event in self.pendingEvent.events.items():
            event.transform(self, date, period)
        self.data.append(self.pendingEvent)
    
    def appendEvent(self, events: EventGroup):
        self.data.append(events)

    def latestEvents(self):
        return self.data[-1]

FinanceEvent = Callable[[FinanceHistory, FinanceState, date, relativedelta], FinanceState]

def constantSalariedIncome(salary: float, accrualModel: AccrualModel) -> FinanceEvent:
    def incomeEvent(history: FinanceHistory,
                    state: FinanceState,
                    date: date,
                    period: relativedelta) -> FinanceState:
        result = state.copy()
        portion = portionOfYear(date, period, accrualModel)
        result.cash += salary * portion
        result.taxableIncome += salary * portion
        return result
    return incomeEvent

def constantExpense(yearlyExpense: float, accrualModel: AccrualModel) -> FinanceEvent:
    def expenseEvent(history: FinanceHistory,
                     state: FinanceState,
                     date: date,
                     period: relativedelta) -> FinanceState:
        result = state.copy()
        result.cash -= yearlyExpense * portionOfYear(date, period, accrualModel)
        return result
    return expenseEvent

def appreciateConstantAssets(history: FinanceHistory,
                             state: FinanceState,
                             date: date,
                             period: relativedelta) -> FinanceState:
    result = state.copy()
    result.constantGrowthAssets = [asset.appreciate(date, period) for asset
                                   in result.constantGrowthAssets]
    return result

def makeAmortizedPayments(history: FinanceHistory,
                          state: FinanceState,
                          date: date,
                          period: relativedelta) -> FinanceState:
    result = state.copy()
    for name, amortizingLoan in result.amortizingLoans.items():
        newLoan = amortizingLoan.copy()
        yearFraction = portionOfYear(date, period, amortizingLoan.accrualModel)
        adjustedRate = pow(1 + newLoan.rate, yearFraction) - 1
        interestPaid = (newLoan.loanAmount - newLoan.principle) * adjustedRate
        if newLoan.payment < 0:
            denominator = 1 - pow(1 + adjustedRate, -(newLoan.term / yearFraction))
            paymentAmount = interestPaid / denominator
            newLoan.payment = paymentAmount
        newLoan.principle += newLoan.payment - interestPaid
        newLoan.term -= yearFraction
        result.cash -= newLoan.payment
        result.amortizingLoans[name] = newLoan
    return result

def balanceComponents(history: FinanceHistory) -> list[FinanceEvent]:
    if history.events:
        raise RuntimeError('balanceComponents should only be called on FinanceHistory objects that have no events')
    
    latestState = history.latestState()
    components: list[FinanceEvent] = []
    
    if latestState.amortizingLoans:
        components.append(makeAmortizedPayments)
    if latestState.constantGrowthAssets:
        components.append(appreciateConstantAssets)
    return components

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
