from __future__ import annotations
from ctypes import ArgumentError

import sys
import abc

from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta
from enum import Enum
from math import pow
from typing import Callable

from .scheduling import AccrualModel, portionOfYear

class AbstractEvent(abc.ABC):
    '''
    "FinanceEvent" is a good name, but that's already taken. This should deprecate/rebase
    a lot of FinanceState and FinanceEvent. They can keep their names in the meantime.
    '''
    class EventType(Enum):
        Undefined = 0
        Cash = 1
        ConstantGrowthAsset = 2
        AmortizingLoan = 3
    
    name: str
    eventType: EventType = EventType.Undefined

    @abc.abstractmethod
    def passEvent(self,
                  history: FinanceHistory,
                  date: date,
                  delta: relativedelta) -> AbstractEvent:
        raise NotImplementedError()

    @abc.abstractmethod
    def copy(self) -> AbstractEvent:
        raise NotImplementedError()

class EventGroup(object):
    date: date
    events: dict[str, AbstractEvent]

    def copy(self):
        result = EventGroup()
        result.date = self.date
        result.events = { name: event.copy() for name, event in self.events.items() }
        return result

class CashEvent(AbstractEvent):
    def __init__(self, name: str, value: float):
        self.name = name
        self.value = value
        self.eventType = self.EventType.Cash

    def passEvent(self,
                  history: FinanceHistory,
                  date: date,
                  delta: relativedelta) -> CashEvent:
        return self.copy()

    def copy(self):
        return CashEvent(self.name, self.value)

class ConstantGrowthAsset(AbstractEvent):
    '''
    "Constant" really means constant exponential rate
    '''
    value: float
    appreciation: float
    
    def __init__(self, name: str, accrualModel: AccrualModel, initialValue: float = 0, annualAppreciation: float = 0):
        self.name = name
        self.value = initialValue
        self.appreciation = annualAppreciation
        self.accrualModel = accrualModel
        self.eventType = self.EventType.ConstantGrowthAsset

    def passEvent(self,
                  history: FinanceHistory,
                  date: date,
                  delta: relativedelta) -> ConstantGrowthAsset:
        portion = portionOfYear(date, delta, self.accrualModel)
        value = self.value * pow(1 + self.appreciation, portion)
        return ConstantGrowthAsset(self.name, self.accrualModel, value, self.appreciation)

    def copy(self) -> ConstantGrowthAsset:
        result = ConstantGrowthAsset(self.name, self.accrualModel, self.value, self.appreciation)
        return result

    def __str__(self) -> str:
        return str(self.value)

def addToCash(events: EventGroup, difference: float) -> EventGroup:
    result = events.copy()
    if difference < 0:
        for _, event in result.events.items():
            if isinstance(event, CashEvent):
                if event.value >= difference:
                    event.value -= difference
                    difference = 0
                elif event.value > 0:
                    difference -= event.value
                    event.value = 0
        if difference > 0:
            raise RuntimeError("not enough money to subtract")
    else:
        for _, event in result.events.items():
            if difference > -0.0001 and difference < 0.0001:
                break
            if isinstance(event, CashEvent):
                event.value += difference
                difference = 0
    return result

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

    def passEvent(self,
                  history: FinanceHistory,
                  date: date,
                  period: relativedelta) -> AmortizingLoan:
        result = self.copy()
        # for name, amortizingLoan in result.amortizingLoans.items():
        yearFraction = portionOfYear(date, period, self.accrualModel)
        adjustedRate = pow(1 + result.rate, yearFraction) - 1
        interestPaid = (result.loanAmount - result.principle) * adjustedRate
        if result.payment < 0:
            denominator = 1 - pow(1 + adjustedRate, -(result.term / yearFraction))
            paymentAmount = interestPaid / denominator
            result.payment = paymentAmount
        result.principle += result.payment - interestPaid
        result.term -= yearFraction
        addToCash(history.pendingEvent, -result.payment)
        return result

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

    def passEvent(self,
                  history: FinanceHistory,
                  date: date,
                  period: relativedelta) -> ConstantSalariedIncome:
        portion = portionOfYear(date, period, self.accrualModel)
        addToCash(history.pendingEvent, portion * self.salary)
        return self

    def copy(self):
        return ConstantSalariedIncome(self.name, self.salary, self.accrualModel)

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

    # def setEventComponents(self, events: list[FinanceEvent]):
    #     self.events = events

    def passEvent(self, date: date, period: relativedelta):
        self.pendingEvent = self.data[-1].copy()
        self.pendingEvent.date = date
        for name in self.pendingEvent.events:
            self.pendingEvent.events[name] = self.pendingEvent.events[name].passEvent(self, date, period)
        self.data.append(self.pendingEvent)
    
    def appendEvent(self, events: EventGroup):
        self.data.append(events)

    def latestState(self):
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

@dataclass
class TaxBracket(object):
    rate: float
    income: float

def taxPaymentSchedule(frequency: relativedelta,
                       accrualModel: AccrualModel,
                       brackets: list[TaxBracket]) -> FinanceEvent:
    if len(brackets) < 1:
        raise ArgumentError('there must be at least one tax bracket')
    if brackets[0].income != 0.0:
        raise ArgumentError('brackets must start with a zero income bracket')

    def payTaxes(history: FinanceHistory,
                 state: FinanceState,
                 date: date,
                 period: relativedelta) -> FinanceState:
        result = state.copy()
        if (date - period) <= (date - frequency):
            taxDue = 0
            for bracket in brackets[::-1]:
                adjustedIncomeThreshold = bracket.income * portionOfYear(date,
                                                                         period,
                                                                         accrualModel)
                if result.taxableIncome > adjustedIncomeThreshold:
                    marginAboveBracket = result.taxableIncome - adjustedIncomeThreshold
                    taxDue += bracket.rate * marginAboveBracket
                    result.taxableIncome -= marginAboveBracket
            result.cash -= taxDue
            result.taxesPaid += taxDue
        return result

    return payTaxes

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
