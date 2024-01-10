from __future__ import annotations
from ctypes import ArgumentError

import sys

from datetime import date
from dateutil.relativedelta import relativedelta
from math import pow
from typing import Callable

from .scheduling import AccrualModel, portionOfYear
from .util import parseAccrualModel

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
