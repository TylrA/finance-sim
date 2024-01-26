import pytest
from finance_sim import *
from ctypes import ArgumentError
from datetime import date
from dateutil.relativedelta import relativedelta


def testSalariedIncomeFlatTax():
    delta = relativedelta(months=1)
    events = {
        "i": ConstantSalariedIncome(None, "i", 100000, AccrualModel.PeriodicMonthly),
        "t": TaxPaymentEventProfile(
            None,
            "t",
            delta,
            AccrualModel.PeriodicMonthly,
            [TaxBracket(rate=0.05, income=0)],
        ),
        "c": CashEventProfile(None, "c", 0),
    }
    history = FinanceHistory(EventProfileGroup(date(1999, 12, 1), events))
    for month in range(1, 13):
        history.passEvent(date(2000, month, 1), delta)
    assert history.latestEvents().events["c"].value == pytest.approx(100000 * (1 - 0.05))
    assert history.latestEvents().events["t"].taxableIncome == pytest.approx(0)
    assert history.latestEvents().events["t"].taxesPaid == pytest.approx(5000)


def testIsolatedTaxableIncome():
    delta = relativedelta(years=1)
    events = {
        "t": TaxPaymentEventProfile(
            None, "t", delta, AccrualModel.PeriodicYearly, [TaxBracket(rate=0.05, income=0)]
        ),
        "c": CashEventProfile(None, "c", 100000),
    }
    history = FinanceHistory(EventProfileGroup(date(1999, 1, 1), events))
    history.latestEvents().events["t"].taxableIncome = 100000
    history.passEvent(date(2000, 1, 1), delta)
    assert history.latestEvents().events["c"].value == pytest.approx(100000 * (1 - 0.05))
    assert history.latestEvents().events["t"].taxableIncome == pytest.approx(0)
    assert history.latestEvents().events["t"].taxesPaid == pytest.approx(5000)


def testMultipleTaxBrackets():
    delta = relativedelta(years=1)
    events = {
        "t": TaxPaymentEventProfile(
            None,
            "t",
            delta,
            AccrualModel.PeriodicYearly,
            [TaxBracket(0.05, 0), TaxBracket(0.10, 40000), TaxBracket(0.20, 60000)],
        ),
        "c": CashEventProfile(None, "c", 100000),
    }
    history = FinanceHistory(EventProfileGroup(date(1999, 1, 1), events))
    history.latestEvents().events["t"].taxableIncome = 100000
    history.passEvent(date(2000, 1, 1), delta)
    expectedTaxPaid = 40000 * 0.05 + 20000 * 0.10 + 40000 * 0.20
    assert history.latestEvents().events["c"].value == pytest.approx(
        100000 - expectedTaxPaid
    )
    assert history.latestEvents().events["t"].taxableIncome == pytest.approx(0)
    assert history.latestEvents().events["t"].taxesPaid == pytest.approx(expectedTaxPaid)


def testMissingTaxBrackets():
    with pytest.raises(ArgumentError):
        TaxPaymentEventProfile(
            None, "t", relativedelta(months=1), AccrualModel.PeriodicMonthly, []
        )


def testNonZeroTaxBracket():
    with pytest.raises(ArgumentError):
        TaxPaymentEventProfile(
            None,
            "t",
            relativedelta(months=1),
            AccrualModel.PeriodicMonthly,
            [TaxBracket(rate=0.05, income=10)],
        )
