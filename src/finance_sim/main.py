from __future__ import annotations
from ctypes import ArgumentError

from typing import Callable
from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta
from calendar import isleap
from enum import Enum
import sys
import calendar

class AccrualModel(Enum):
    ProRata = 0
    PeriodicMonthly = 1
    PeriodicWeekly = 2
    PeriodicBiweekly = 3
    PeriodicSemiMonthly = 4

def nonZeroValuesInDelta(delta: relativedelta) -> list[str]:
    result: list[str] = []
    if delta.years != 0: result.append('years')
    if delta.months != 0: result.append('months')
    if delta.days != 0: result.append('days')
    if delta.leapdays != 0: result.append('leapdays')
    if delta.hours != 0: result.append('hours')
    if delta.minutes != 0: result.append('minutes')
    if delta.seconds != 0: result.append('seconds')
    if delta.microseconds != 0: result.append('microseconds')
    return result

def portionOfYear(date: date, period: relativedelta, accrualModel: AccrualModel) -> float:
    fieldsInPeriod = nonZeroValuesInDelta(period)
    if accrualModel == AccrualModel.PeriodicMonthly:
        if fieldsInPeriod != ['months'] and fieldsInPeriod != ['years', 'months']:
            raise ArgumentError("Periodic monthly accrual model does not support periods " +
                                "containing non-month, non-year values")
        return period.years + period.months / 12
    elif accrualModel == AccrualModel.PeriodicWeekly:
        if fieldsInPeriod != ['days']:
            raise ArgumentError("Periodic weekly accrual model does not support periods " +
                                "containing non-day values")
        if period.days % 7:
            raise ArgumentError("Periodic weekly accrual model only works for periods " +
                                "that are multiples of 7 days")
        return (period.days // 7) / 52
    elif accrualModel == AccrualModel.PeriodicBiweekly:
        if fieldsInPeriod != ['days']:
            raise ArgumentError("Periodic biweekly accrual model does not support " +
                                "periods containing non-day values")
        if period.days % 14:
            raise ArgumentError("Periodic weekly accrual model only works for periods " +
                                "that are multiples of 14 days")
        return (period.days // 14) / 26
    elif accrualModel == AccrualModel.PeriodicSemiMonthly:
        daysInMonth = calendar.monthrange(date.year, date.month)[1]
        if (
            fieldsInPeriod != ['days'] and fieldsInPeriod != ['months', 'days'] and \
            fieldsInPeriod != ['years', 'months', 'days']
        ):
            raise ArgumentError("Periodic semi-monthly accrual model does not support " +
                                "periods containing non-day, non-month, non-year values")
        if date.day != 15 and date.day != daysInMonth:
            raise ArgumentError("Periodic semi-monthly accrual model does not support " +
                                "dates not on the 15th or final day of the month")
        dateBeginningPeriod = date - period
        daysInMonthBeginning = calendar.monthrange(dateBeginningPeriod.year,
                                                   dateBeginningPeriod.month)[1]
        if dateBeginningPeriod != 15 and dateBeginningPeriod != daysInMonthBeginning:
            raise ArgumentError("Periodic semi-monthly accrual model requires that the " +
                                "date that would begin the period be on the 15th or " +
                                "final day of the month")
        periods = (date.year - dateBeginningPeriod.year) * 24
        periods += (date.month - dateBeginningPeriod.month) * 2
        if date.day == daysInMonth and dateBeginningPeriod.day == 15:
            periods += 1
        elif date.day == 15 and dateBeginningPeriod.day == daysInMonthBeginning:
            periods -= 1
        return periods / 24

    # pro rata
    periodStart = date - period
    days = date.toordinal() - periodStart.toordinal()
    daysInYear = 366 if isleap(date.year) else 365
    return days / daysInYear

class ConstantGrowthAsset(object):
    '''
    "Constant" really means constant exponential rate
    '''
    value: float
    appreciation: float
    
    def __init__(self, accrualModel: AccrualModel, initialValue: float = 0, annualAppreciation: float = 0):
        self.value = initialValue
        self.appreciation = annualAppreciation
        self.accrualModel = accrualModel

    def appreciate(self, date: date, period: relativedelta) -> ConstantGrowthAsset:
        portion = portionOfYear(date, period, self.accrualModel)
        value = self.value * (1 + self.appreciation) ** portion
        return ConstantGrowthAsset(value, self.appreciation)

class AmortizingLoan(object):
    def __init__(self,
                 name: str,
                 accrualModel: AccrualModel,
                 initialPrinciple: float = 0,
                 loanAmount: float = 0,
                 rate: float = 0.05,
                 remainingTermInYears: float = 20):
        self.name = name
        self.accrualModel = accrualModel
        self.principle = initialPrinciple
        self.loanAmount = loanAmount
        self.rate = rate
        self.term = remainingTermInYears

    def copy(self):
        result = AmortizingLoan(self.name,
                                self.accrualModel,
                                self.principle,
                                self.loanAmount,
                                self.rate,
                                self.term)
        return result
        

class FinanceState(object):
    def __init__(self, date: date = date.today()):
        self.date = date
        self.cash: float = 0
        self.constantGrowthAssets: list[ConstantGrowthAsset] = []
        self.amortizingLoans: dict[str, AmortizingLoan] = {}
        self.taxableIncome: float = 0
        self.taxesPaid: float = 0
        self.lastDateTaxesPaid: date = date

    def copy(self):
        result = FinanceState()
        result.date = self.date
        result.cash = self.cash
        result.constantGrowthAssets = self.constantGrowthAssets
        result.amortizingLoans = self.amortizingLoans
        result.taxableIncome = self.taxableIncome
        result.taxesPaid = self.taxesPaid
        result.lastDateTaxesPaid = self.lastDateTaxesPaid
        return result

class FinanceHistory(object):
    def __init__(self, event: FinanceState):
        self.data: list[FinanceState] = [event]

    def setEventComponents(self, events: list[FinanceEvent]):
        self.events = events

    def passEvent(self, date: date, period: relativedelta):
        newState = self.data[-1].copy()
        newState.date = date
        for event in self.events:
            newState = event(self, newState, date, period)
        self.data.append(newState)
    
    def appendEvent(self, event: FinanceState):
        self.data.append(event)

    def latestEvent(self):
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

def taxPaymentSchedule(frequency: relativedelta,
                       brackets: list[TaxBracket]) -> FinanceEvent:
    if len(brackets) < 1:
        raise RuntimeError('there must be at least one tax bracket')
    if brackets[0].income != 0.0:
        raise RuntimeError('brackets must start with a zero income bracket')

    def payTaxes(history: FinanceHistory,
                 state: FinanceState,
                 date: date,
                 period: relativedelta) -> FinanceState:
        result = state.copy()
        taxPeriod = relativedelta(seconds=int((date - result.lastDateTaxesPaid)
                                              .total_seconds()))
        if (date - taxPeriod) <= (date - frequency):
            taxDue = 0
            for bracket in brackets[::-1]:
                adjustedIncomeThreshold = bracket.income * portionOfYear(date, taxPeriod)
                if result.taxableIncome > adjustedIncomeThreshold:
                    marginAboveBracket = result.taxableIncome - adjustedIncomeThreshold
                    taxDue += bracket.rate * marginAboveBracket
                    result.taxableIncome -= marginAboveBracket
            result.cash -= taxDue
            result.taxesPaid += taxDue
            result.lastDateTaxesPaid = date
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
