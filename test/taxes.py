import pytest
from finance_sim import *

def testSalariedIncomeFlatTax():
    history = FinanceHistory(FinanceState(0))
    history.setEventComponents(
        [constantSalariedIncome(100000),
         taxPaymentSchedule(1 / 12, [TaxBracket(rate = 0.05, income = 0)])])
    for i in range(12):
        history.passEvent(i + 1, 1 / 12)
    assert history.latestEvent().cash == pytest.approx(100000 * (1 - 0.05))
    assert history.latestEvent().taxableIncome == pytest.approx(0)
    assert history.latestEvent().taxesPaid == pytest.approx(5000)

def testIsolatedTaxableIncome():
    history = FinanceHistory(FinanceState(0))
    history.setEventComponents(
        [taxPaymentSchedule(1 / 12, [TaxBracket(rate = 0.05, income = 0)])])
    history.latestEvent().taxableIncome = 100000
    history.passEvent(1, 1)
    assert history.latestEvent().cash == pytest.approx(100000 * (- 0.05))
    assert history.latestEvent().taxableIncome == pytest.approx(0)
    assert history.latestEvent().taxesPaid == pytest.approx(5000)

def testMultipleTaxBrackets():
    history = FinanceHistory(FinanceState(0))
    history.setEventComponents(
        [taxPaymentSchedule(1 / 12,
                            [TaxBracket(rate = 0.05, income = 0),
                             TaxBracket(rate = 0.10, income = 40000),
                             TaxBracket(rate = 0.20, income = 60000)])])
    history.latestEvent().taxableIncome = 100000
    history.passEvent(1, 1)
    expectedTaxPaid = 40000 * 0.05 + 20000 * 0.10 + 40000 * 0.20
    assert history.latestEvent().cash == pytest.approx(-expectedTaxPaid)
    assert history.latestEvent().taxableIncome == pytest.approx(0)
    assert history.latestEvent().taxesPaid == pytest.approx(expectedTaxPaid)

def testMissingTaxBrackets():
    with pytest.raises(RuntimeError):
        history = FinanceHistory(FinanceState(0))
        history.setEventComponents([taxPaymentSchedule(1 / 12, [])])
        history.latestEvent().taxableIncome = 100000
        history.passEvent(1, 1 / 12)

def testNonZeroTaxBracket():
    with pytest.raises(RuntimeError):
        history = FinanceHistory(FinanceState(0))
        history.setEventComponents(
            [taxPaymentSchedule(1 / 12, [TaxBracket(rate = 0.05, income = 10)])])
        history.latestEvent().taxableIncome = 100000
        history.passEvent(1, 1 / 12)
