from __future__ import annotations

import abc

from ctypes import ArgumentError
from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import Any, Optional, Type

from .scheduling import AccrualModel, portionOfYear
from .util import parseAccrualModel

EventConfigType = Optional[dict[str, Any]]


class AbstractEventProfile(abc.ABC):
    """
    "FinanceEvent" is a good name, but that's already taken. This should deprecate/rebase
    a lot of FinanceState and FinanceEvent. They can keep their names in the meantime.
    """

    name: str

    @abc.abstractmethod
    def __init__(self, config: EventConfigType, name: str, **kwargs):
        raise NotImplementedError()

    @abc.abstractmethod
    def transform(self, history: FinanceHistory, date: date, delta: relativedelta) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def copy(self) -> AbstractEventProfile:
        raise NotImplementedError()


abstractEventProfileType: dict[str, Type[AbstractEventProfile]] = {}


class EventProfileGroup(object):
    date: date
    events: dict[str, AbstractEventProfile]

    def __init__(self, date: date, events: dict[str, AbstractEventProfile]):
        self.date = date
        self.events = events

    def copy(self):
        return EventProfileGroup(
            self.date, {name: event.copy() for name, event in self.events.items()}
        )


class CashEventProfile(AbstractEventProfile):
    value: float

    def __init__(self, config: EventConfigType, name: str, value: float = 0):
        self.name = name
        if config is not None:
            self.value = float(config["value"])
        self.value = value

    def transform(self, history: FinanceHistory, date: date, delta: relativedelta):
        pass

    def copy(self):
        return CashEventProfile(None, self.name, self.value)

    def __str__(self):
        return str(round(self.value, 2))


abstractEventProfileType["cash"] = CashEventProfile


@dataclass
class TaxBracket(object):
    rate: float
    income: float


class TaxPaymentEventProfile(AbstractEventProfile):
    frequency: relativedelta
    accrualModel: AccrualModel
    brackets: list[TaxBracket]
    taxableIncome: float
    taxesPaid: float

    def __init__(
        self,
        config: EventConfigType,
        name: str,
        frequency: relativedelta = relativedelta(months=1),
        accrualModel: AccrualModel = AccrualModel.PeriodicMonthly,
        brackets: list[TaxBracket] = [],
    ):
        if config is not None:
            frequency = config["frequency"]
            accrualModel = parseAccrualModel(config["accrualModel"])
            brackets = config["brackets"]  # todo: same as above
        if len(brackets) < 1:
            raise ArgumentError("there must be at least one tax bracket")
        if brackets[0].income != 0.0:
            raise ArgumentError("brackets must start with ha zero income bracket")

        self.name = name
        self.frequency = frequency
        self.accrualModel = accrualModel
        self.brackets = brackets
        self.taxableIncome = 0
        self.taxesPaid = 0

    def transform(self, history: FinanceHistory, date: date, delta: relativedelta):
        if (date - delta) <= (date - self.frequency):
            taxDue = 0
            for bracket in self.brackets[::-1]:
                adjustedIncomeThreshold = bracket.income * portionOfYear(
                    date, delta, self.accrualModel
                )
                if self.taxableIncome > adjustedIncomeThreshold:
                    marginAboveBracket = self.taxableIncome - adjustedIncomeThreshold
                    taxDue += bracket.rate * marginAboveBracket
                    self.taxableIncome -= marginAboveBracket
            addToCash(history.pendingEvents, -taxDue)
            self.taxesPaid += taxDue

    def copy(self):
        result = TaxPaymentEventProfile(
            None, self.name, self.frequency, self.accrualModel, self.brackets
        )
        result.taxableIncome = self.taxableIncome
        result.taxesPaid = self.taxesPaid
        return result

    def __str__(self):
        return "taxable income: {}; taxes paid: {}".format(
            self.taxableIncome, self.taxesPaid
        )


abstractEventProfileType["tax-payment"] = TaxPaymentEventProfile


class ConstantGrowthAsset(AbstractEventProfile):
    """
    "Constant" really means constant exponential rate
    """

    value: float
    appreciation: float

    def __init__(
        self,
        config: EventConfigType,
        name: str,
        accrualModel: AccrualModel = AccrualModel.PeriodicMonthly,
        initialValue: float = 0,
        annualAppreciation: float = 0,
    ):
        if config is not None:
            accrualModel = parseAccrualModel(config["accrualModel"])
            initialValue = config["initialValue"]
            annualAppreciation = config["annualAppreciation"]
        self.name = name
        self.value = initialValue
        self.appreciation = annualAppreciation
        self.accrualModel = accrualModel

    def transform(self, history: FinanceHistory, date: date, delta: relativedelta):
        portion = portionOfYear(date, delta, self.accrualModel)
        self.value *= pow(1 + self.appreciation, portion)

    def copy(self) -> ConstantGrowthAsset:
        result = ConstantGrowthAsset(
            None, self.name, self.accrualModel, self.value, self.appreciation
        )
        return result

    def __str__(self) -> str:
        return str(round(self.value, 2))


abstractEventProfileType["constant-growth-asset"] = ConstantGrowthAsset


def addToCash(events: EventProfileGroup, difference: float, taxable: bool = True) -> None:
    if difference < 0:
        for _, event in events.events.items():
            if isinstance(event, CashEventProfile):
                if event.value >= -difference:
                    event.value += difference
                    difference = 0
                elif event.value > 0:
                    difference += event.value
                    event.value = 0
        if difference > 0:
            raise RuntimeError("not enough money to subtract")
    else:
        cashEventProfile: Optional[CashEventProfile] = None
        taxPaymentEventProfile: Optional[TaxPaymentEventProfile] = None
        for _, event in events.events.items():
            if isinstance(event, CashEventProfile):
                cashEventProfile = event
                if taxPaymentEventProfile:
                    break
            elif isinstance(event, TaxPaymentEventProfile):
                taxPaymentEventProfile = event
                if cashEventProfile:
                    break
        if cashEventProfile:
            cashEventProfile.value += difference
        if taxable and taxPaymentEventProfile:
            taxPaymentEventProfile.taxableIncome += difference


class AmortizingLoan(AbstractEventProfile):
    accrualModel: AccrualModel
    principle: float
    loanAmount: float
    rate: float
    term: float
    payment: float

    def __init__(
        self,
        config: EventConfigType,
        name: str,
        accrualModel: AccrualModel = AccrualModel.PeriodicMonthly,
        initialPrinciple: float = 0,
        loanAmount: float = 0,
        rate: float = 0.05,
        remainingTermInYears: float = 20,
        payment: float = -1,
    ):
        if config is not None:
            accrualModel = parseAccrualModel(config["accrualModel"])
            initialPrinciple = config["initialPrinciple"]
            loanAmount = config["loanAmount"]
            rate = config["rate"]
            remainingTermInYears = config["remainingTermInYears"]
            payment = config["payment"]
        self.name = name
        self.accrualModel = accrualModel
        self.principle = initialPrinciple
        self.loanAmount = loanAmount
        self.rate = rate
        self.term = remainingTermInYears
        self.payment = payment

    def transform(self, history: FinanceHistory, date: date, period: relativedelta) -> None:
        yearFraction = portionOfYear(date, period, self.accrualModel)
        adjustedRate = pow(1 + self.rate, yearFraction) - 1
        interestPaid = (self.loanAmount - self.principle) * adjustedRate
        if self.payment < 0:
            denominator = 1 - pow(1 + adjustedRate, -(self.term / yearFraction))
            paymentAmount = interestPaid / denominator
            self.payment = paymentAmount
        self.principle += self.payment - interestPaid
        self.term -= yearFraction
        addToCash(history.pendingEvents, -self.payment)

    def copy(self):
        result = AmortizingLoan(
            None,
            self.name,
            self.accrualModel,
            self.principle,
            self.loanAmount,
            self.rate,
            self.term,
            self.payment,
        )
        return result

    def __str__(self):
        return str(self.principle)


abstractEventProfileType["amortizing-loan"] = AmortizingLoan


class ConstantSalariedIncome(AbstractEventProfile):
    salary: float
    accrualModel: AccrualModel

    def __init__(
        self,
        config: EventConfigType,
        name: str,
        salary: float = 0,
        accrualModel: AccrualModel = AccrualModel.PeriodicMonthly,
    ):
        if config is not None:
            salary = config["salary"]
            accrualModel = parseAccrualModel(config["accrualModel"])
        self.name = name
        self.salary = salary
        self.accrualModel = accrualModel

    def transform(self, history: FinanceHistory, date: date, period: relativedelta):
        portion = portionOfYear(date, period, self.accrualModel)
        addToCash(history.pendingEvents, portion * self.salary)

    def copy(self):
        return ConstantSalariedIncome(None, self.name, self.salary, self.accrualModel)

    def __str__(self):
        return str(self.salary)


abstractEventProfileType["constant-salaried-income"] = ConstantSalariedIncome


class ConstantExpense(AbstractEventProfile):
    yearlyExpense: float
    accrualModel: AccrualModel

    def __init__(
        self,
        config: EventConfigType,
        name: str,
        yearlyExpense: float = 0,
        accrualModel: AccrualModel = AccrualModel.PeriodicMonthly,
    ):
        if config is not None:
            yearlyExpense = config["yearlyExpense"]
            accrualModel = parseAccrualModel(config["accrualModel"])
        self.name = name
        self.yearlyExpense = yearlyExpense
        self.accrualModel = accrualModel

    def transform(self, history: FinanceHistory, date: date, period: relativedelta):
        portion = portionOfYear(date, period, self.accrualModel)
        addToCash(history.pendingEvents, -portion * self.yearlyExpense)

    def copy(self):
        return ConstantExpense(None, self.name, self.yearlyExpense, self.accrualModel)

    def __str__(self):
        return str(-self.yearlyExpense)


abstractEventProfileType["constant-expense"] = ConstantExpense


class FinanceState(object):
    def __init__(self, date: date = date.today()):
        self.date = date
        self.cash: float = 0
        self.constantGrowthAssets: list[ConstantGrowthAsset] = []
        self.amortizingLoans: dict[str, AmortizingLoan] = {}
        self.taxableIncome: float = 0
        self.taxesPaid: float = 0

    def copy(self):
        result = FinanceState()
        result.date = self.date
        result.cash = self.cash
        result.constantGrowthAssets = self.constantGrowthAssets
        result.amortizingLoans = self.amortizingLoans
        result.taxableIncome = self.taxableIncome
        result.taxesPaid = self.taxesPaid
        return result


class FinanceHistory(object):
    pendingEvents: EventProfileGroup

    def __init__(self, event: EventProfileGroup):
        self.data: list[EventProfileGroup] = [event]

    def _startPendingEventProfile(self, date: date):
        self.pendingEvents = self.data[-1].copy()
        self.pendingEvents.date = date

    def _processAndPushPending(self, date: date, period: relativedelta):
        for _, event in self.pendingEvents.events.items():
            event.transform(self, date, period)
        self.data.append(self.pendingEvents)

    def passEvent(self, date: date, period: relativedelta):
        self._startPendingEventProfile(date)
        self._processAndPushPending(date, period)

    def appendEvent(self, events: EventProfileGroup):
        self.data.append(events)

    def latestEvents(self):
        return self.data[-1]
