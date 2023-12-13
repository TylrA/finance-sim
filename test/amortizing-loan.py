import pytest
from finance_sim import *
from datetime import date
from dateutil.relativedelta import relativedelta

def testAmortizingLoanTerm():
    loan = AmortizingLoan(None, 'test', AccrualModel.PeriodicMonthly, 0, 100000, 0.05, 20)
    eventGroup = EventGroup(date(1999, 12, 1), {'test': loan,
                                                'cash': CashEvent(None, 'cash', 600000)})
    history = FinanceHistory(eventGroup)
    delta = relativedelta(months=1)
    history.passEvent(date(2000, 1, 1), delta)
    event = history.latestEvents().events['test']
    assert isinstance(event, AmortizingLoan)
    assert event.term == pytest.approx(20 - 1 / 12)
    for month in range(2, 13):
        history.passEvent(date(2000, month, 1), delta)
    event = history.latestEvents().events['test']
    assert isinstance(event, AmortizingLoan)
    assert event.term == pytest.approx(19)

def testAmortizingLoanFullPayment():
    loan = AmortizingLoan(None, 'test', AccrualModel.PeriodicMonthly, 0, 100000, 0.05, 20)
    eventGroup = EventGroup(date(1999, 12, 1), { 'test': loan,
                                                 'cash': CashEvent(None, 'cash', 600000) })
    history = FinanceHistory(eventGroup)
    event = history.latestEvents().events['test']
    assert isinstance(event, AmortizingLoan)
    assert event.principle == 0
    delta = relativedelta(months=1)
    for year in range(2000,2020):
        for month in range(1, 13):
            history.passEvent(date(year, month, 1), delta)
    event = history.latestEvents().events['test']
    assert isinstance(event, AmortizingLoan)
    assert event.principle == pytest.approx(100000)

def testAmortizingLoanConstantPaymentCost():
    loan = AmortizingLoan(None, 'test', AccrualModel.PeriodicMonthly, 0, 100000, 0.05, 20)
    eventGroup = EventGroup(date(1999, 12, 1), { 'test': loan,
                                                 'cash': CashEvent(None, 'cash', 600000) })
    history = FinanceHistory(eventGroup)
    delta = relativedelta(months=1)
    history.passEvent(date(2000, 1, 1), delta)
    previousCash = history.latestEvents().events['cash']
    assert isinstance(previousCash, CashEvent)
    paymentAmount = 600000 - previousCash.value
    for month in range(2, 13):
        history.passEvent(date(2000, month, 1), delta)
        newCash = history.latestEvents().events['cash']
        assert isinstance(newCash, CashEvent)
        assert previousCash.value - newCash.value == pytest.approx(paymentAmount, 1e-3)
        previousCash = newCash

def testAmortizingLoanInterestRate():
    loan = AmortizingLoan(None, 'test', AccrualModel.PeriodicMonthly, 0, 100000, 0.05, 20)
    eventGroup = EventGroup(date(2000, 1, 1), { 'test': loan,
                                                 'cash': CashEvent(None, 'cash', 600000) })
    history = FinanceHistory(eventGroup)
    delta = relativedelta(years=1)
    history.passEvent(date(2001, 1, 1), delta)
    cashEvent = history.latestEvents().events['cash']
    assert isinstance(cashEvent, CashEvent)
    paymentAmount = 600000 - cashEvent.value
    loanEvent = history.latestEvents().events['test']
    assert isinstance(loanEvent, AmortizingLoan)
    interestPayment = paymentAmount - loanEvent.principle
    assert interestPayment == pytest.approx(100000 * 0.05, 1e-6)
