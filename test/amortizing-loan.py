import pytest
from finance_sim import *
from datetime import date
from dateutil.relativedelta import relativedelta

def testAmortizingLoanTerm():
    loan = AmortizingLoan('test', AccrualModel.PeriodicMonthly, 0, 100000, 0.05, 20)
    state = FinanceState(date(1999, 12, 1))
    state.cash = 100000
    history = FinanceHistory(state)
    state.amortizingLoans['test'] = loan
    delta = relativedelta(months=1)
    state = makeAmortizedPayments(history, state, date(2000, 1, 1), delta)
    assert state.amortizingLoans['test'].term == pytest.approx(20 - 1 / 12)
    for month in range(2, 13):
        state = makeAmortizedPayments(history, state, date(2000, month, 1), delta)
    assert state.amortizingLoans['test'].term == pytest.approx(19)

def testAmortizingLoanFullPayment():
    loan = AmortizingLoan('test', AccrualModel.PeriodicMonthly, 0, 100000, 0.05, 20)
    state = FinanceState(date(1999, 12, 1))
    state.cash = 600000
    history = FinanceHistory(state)
    state.amortizingLoans['test'] = loan
    assert state.amortizingLoans['test'].principle == 0
    delta = relativedelta(months=1)
    for year in range(2000,2020):
        for month in range(1, 13):
            state = makeAmortizedPayments(history, state, date(year, month, 1), delta)
    assert state.amortizingLoans['test'].principle == pytest.approx(100000)

def testAmortizingLoanConstantPaymentCost():
    loan = AmortizingLoan('test', AccrualModel.PeriodicMonthly, 0, 100000, 0.05, 20)
    state = FinanceState(date(1999, 12, 1))
    state.cash = 600000
    history = FinanceHistory(state)
    state.amortizingLoans['test'] = loan
    delta = relativedelta(months=1)
    state = makeAmortizedPayments(history, state, date(2000, 1, 1), delta)
    previousCash = state.cash
    paymentAmount = 600000 - previousCash
    for month in range(2, 13):
        state = makeAmortizedPayments(history, state, date(2000, month, 1), delta)
        assert previousCash - state.cash == pytest.approx(paymentAmount, 1e-3)
        previousCash = state.cash

def testAmortizingLoanInterestRate():
    loan = AmortizingLoan('test', AccrualModel.PeriodicYearly, 0, 100000, 0.05, 20)
    state = FinanceState(date(2000, 1, 1))
    state.cash = 600000
    history = FinanceHistory(state)
    state.amortizingLoans['test'] = loan
    state = makeAmortizedPayments(history, state, date(2001, 1, 1), relativedelta(years=1))
    paymentAmount = 600000 - state.cash
    interestPayment = paymentAmount - state.amortizingLoans['test'].principle
    assert interestPayment == pytest.approx(100000 * 0.05, 1e-6)
