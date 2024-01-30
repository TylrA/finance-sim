import pytest
from finance_sim import *
from datetime import date
from dateutil.relativedelta import relativedelta


def testExpenseMonthly():
    initialEvents = {
        "expense": ConstantExpenseEventProfile(
            None, "expense", 120, AccrualModel.PeriodicMonthly
        ),
        "cash": CashEventProfile(None, "cash", 10000),
    }
    eventGroup = EventProfileGroup(date(1999, 12, 1), initialEvents)
    financeData = FinanceHistory(eventGroup)
    delta = relativedelta(months=1)
    financeData.passEvent(date(2000, 1, 1), delta)
    financeData.passEvent(date(2000, 2, 1), delta)
    assert financeData.data[0].events["cash"].value == pytest.approx(10000)
    assert financeData.data[1].events["cash"].value == pytest.approx(9990)
    assert financeData.data[2].events["cash"].value == pytest.approx(9980)


def testExpenseAnnual():
    initialEvents = {
        "expense": ConstantExpenseEventProfile(None, "expense", 120, AccrualModel.ProRata),
        "cash": CashEventProfile(None, "cash", 10000),
    }
    eventGroup = EventProfileGroup(date(2001, 1, 1), initialEvents)
    financeData = FinanceHistory(eventGroup)
    delta = relativedelta(years=1)
    financeData.passEvent(date(2002, 1, 1), delta)
    financeData.passEvent(date(2003, 1, 1), delta)
    assert financeData.data[0].events["cash"].value == pytest.approx(10000)
    assert financeData.data[1].events["cash"].value == pytest.approx(9880)
    assert financeData.data[2].events["cash"].value == pytest.approx(9760)


def testExpenseZero():
    initialEvents = {
        "expense": ConstantExpenseEventProfile(None, "expense", 0, AccrualModel.ProRata),
        "cash": CashEventProfile(None, "cash", 10000),
    }
    eventGroup = EventProfileGroup(date(2001, 1, 1), initialEvents)
    financeData = FinanceHistory(eventGroup)
    delta = relativedelta(years=1)
    financeData.passEvent(date(2002, 1, 1), delta)
    financeData.passEvent(date(2003, 1, 1), delta)
    assert financeData.data[0].events["cash"].value == pytest.approx(10000)
    assert financeData.data[1].events["cash"].value == pytest.approx(10000)
    assert financeData.data[2].events["cash"].value == pytest.approx(10000)
