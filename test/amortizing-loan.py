import pytest
from finance_sim import *

def testAmortizingLoanTerm():
    loan = AmortizingLoan('test', 0, 100000)
    initialState = FinanceState(100000)
    state = loan.makePayment(initialState, 0, 1 / 12)
    assert state.amortizingLoans['test'].term == pytest.approx(20 - 1 / 12)
    for i in range(11):
        state = loan.makePayment(state, i, 1 / 12)
    assert state.amortizingLoans['test'].term == pytest.approx(19)
