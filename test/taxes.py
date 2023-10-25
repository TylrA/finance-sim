import pytest
from finance_sim import *
from ctypes import ArgumentError
from datetime import date
from dateutil.relativedelta import relativedelta

def testSalariedIncomeFlatTax():
    history = FinanceHistory(FinanceState(date(1999, 12, 1)))
    delta = relativedelta(months=1)
    history.setEventComponents(
        [constantSalariedIncome(100000, AccrualModel.PeriodicMonthly),
         taxPaymentSchedule(delta,
                            AccrualModel.PeriodicMonthly,
                            [TaxBracket(rate = 0.05, income = 0)])])
    for month in range(1, 13):
        history.passEvent(date(2000, month, 1), delta)
    assert history.latestEvent().cash == pytest.approx(100000 * (1 - 0.05))
    assert history.latestEvent().taxableIncome == pytest.approx(0)
    assert history.latestEvent().taxesPaid == pytest.approx(5000)

def testIsolatedTaxableIncome():
    history = FinanceHistory(FinanceState(date(1999, 1, 1)))
    delta = relativedelta(years=1)
    history.setEventComponents(
        [taxPaymentSchedule(delta,
                            AccrualModel.PeriodicYearly,
                            [TaxBracket(rate = 0.05, income = 0)])])
    history.latestEvent().taxableIncome = 100000
    history.passEvent(date(2000, 1, 1), delta)
    assert history.latestEvent().cash == pytest.approx(100000 * (- 0.05))
    assert history.latestEvent().taxableIncome == pytest.approx(0)
    assert history.latestEvent().taxesPaid == pytest.approx(5000)

def testMultipleTaxBrackets():
    history = FinanceHistory(FinanceState(date(1999, 1, 1)))
    delta = relativedelta(years=1)
    history.setEventComponents(
        [taxPaymentSchedule(delta,
                            AccrualModel.PeriodicYearly,
                            [TaxBracket(rate = 0.05, income = 0),
                             TaxBracket(rate = 0.10, income = 40000),
                             TaxBracket(rate = 0.20, income = 60000)])])
    history.latestEvent().taxableIncome = 100000
    history.passEvent(date(2000, 1, 1), delta)
    expectedTaxPaid = 40000 * 0.05 + 20000 * 0.10 + 40000 * 0.20
    assert history.latestEvent().cash == pytest.approx(-expectedTaxPaid)
    assert history.latestEvent().taxableIncome == pytest.approx(0)
    assert history.latestEvent().taxesPaid == pytest.approx(expectedTaxPaid)

def testMissingTaxBrackets():
    with pytest.raises(ArgumentError):
        history = FinanceHistory(FinanceState(date(1999, 12, 1)))
        delta = relativedelta(months=1)
        history.setEventComponents([taxPaymentSchedule(delta,
                                                       AccrualModel.PeriodicMonthly,
                                                       [])])
        history.latestEvent().taxableIncome = 100000
        history.passEvent(date(2000, 1, 1), delta)

def testNonZeroTaxBracket():
    with pytest.raises(ArgumentError):
        history = FinanceHistory(FinanceState(date(1999, 12, 1)))
        delta = relativedelta(months=1)
        history.setEventComponents(
            [taxPaymentSchedule(delta,
                                AccrualModel.PeriodicMonthly,
                                [TaxBracket(rate = 0.05, income = 10)])])
        history.latestEvent().taxableIncome = 100000
        history.passEvent(date(2000, 1, 1), delta)
