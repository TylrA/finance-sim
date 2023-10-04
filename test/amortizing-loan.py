import pytest
from finance_sim import *

def testAmortizingLoanTerm():
    loan = AmortizingLoan('test', 0, 100000, 0.05, 20)
    state = FinanceState(100000)
    state.amortizingLoans['test'] = loan
    state = makeAmortizedPayments(state, 0, 1 / 12)
    assert state.amortizingLoans['test'].term == pytest.approx(20 - 1 / 12)
    for i in range(1, 12):
        state = makeAmortizedPayments(state, i, 1 / 12)
    assert state.amortizingLoans['test'].term == pytest.approx(19)

def testAmortizingLoanFullPayment():
    loan = AmortizingLoan('test', 0, 100000, 0.05, 20)
    state = FinanceState(600000)
    state.amortizingLoans['test'] = loan
    assert state.amortizingLoans['test'].principle == 0
    for i in range(12 * 20):
        state = makeAmortizedPayments(state, i, 1 / 12)
    assert state.amortizingLoans['test'].principle == pytest.approx(0)

def testAmortizingLoanConstantPaymentCost():
    loan = AmortizingLoan('test', 0, 100000, 0.05, 20)
    state = FinanceState(600000)
    state.amortizingLoans['test'] = loan
    state = makeAmortizedPayments(state, 0, 1 / 12)
    previousCash = state.cash
    paymentAmount = 600000 - previousCash
    for i in range(10):
        state = makeAmortizedPayments(state, i, 1 / 12)
        assert previousCash - state.cash == pytest.approx(paymentAmount)
        previousCash = state.cash

def testAmortizingLoanInterestRate():
    loan = AmortizingLoan('test', 0, 100000, 0.05, 20)
    state = FinanceState(600000)
    state.amortizingLoans['test'] = loan
    state = makeAmortizedPayments(state, 0, 1)
    paymentAmount = 600000 - state.cash
    interestPayment = paymentAmount - state.amortizingLoans['test'].principle
    assert interestPayment == pytest.approx(600000 * 0.05)
