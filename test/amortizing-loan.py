import pytest
from finance_sim import *

def testAmortizingLoanTerm():
    loan = AmortizingLoan('test', 0, 100000)
    state = FinanceState(100000)
    state.amortizingLoans['test'] = loan
    state = makeAmortizedPayments(state, 0, 1 / 12)
    assert state.amortizingLoans['test'].term == pytest.approx(20 - 1 / 12)
    for i in range(1, 12):
        state = makeAmortizedPayments(state, i, 1 / 12)
    assert state.amortizingLoans['test'].term == pytest.approx(19)

