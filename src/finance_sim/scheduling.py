from calendar import isleap, monthrange
from ctypes import ArgumentError
from dateutil.relativedelta import relativedelta
from datetime import date
from enum import Enum

class AccrualModel(Enum):
    ProRata = 0
    PeriodicMonthly = 1
    PeriodicSemiMonthly = 2
    PeriodicWeekly = 3
    PeriodicBiweekly = 4
    PeriodicYearly = 5

def nonZeroValuesInDelta(delta: relativedelta) -> list[str]:
    result: list[str] = []
    if delta.years != 0: result.append('years')
    if delta.months != 0: result.append('months')
    if delta.days != 0: result.append('days')
    if delta.leapdays != 0: result.append('leapdays')
    if delta.hours != 0: result.append('hours')
    if delta.minutes != 0: result.append('minutes')
    if delta.seconds != 0: result.append('seconds')
    if delta.microseconds != 0: result.append('microseconds')
    return result

def _portionOfYearPeriodicMonthly(date: date, period: relativedelta):
    fieldsInPeriod = nonZeroValuesInDelta(period)
    if fieldsInPeriod != ['months'] and fieldsInPeriod != ['years', 'months']:
        raise ArgumentError("Periodic monthly accrual model does not support periods " +
                            "containing non-month, non-year values")
    return period.years + period.months / 12

def _portionOfYearPeriodicSemiMonthly(date: date, period: relativedelta):
    fieldsInPeriod = nonZeroValuesInDelta
    daysInMonth = monthrange(date.year, date.month)[1]
    dateBeginningPeriod = date - period
    daysInMonthBeginning = monthrange(dateBeginningPeriod.year,
                                      dateBeginningPeriod.month)[1]

    if (
        fieldsInPeriod != ['days'] and fieldsInPeriod != ['months', 'days'] and \
        fieldsInPeriod != ['years', 'months', 'days']
    ):
        raise ArgumentError("Periodic semi-monthly accrual model does not support " +
                            "periods containing non-day, non-month, non-year values")
    if date.day != 15 and date.day != daysInMonth:
        raise ArgumentError("Periodic semi-monthly accrual model does not support " +
                            "dates not on the 15th or final day of the month")
    if dateBeginningPeriod != 15 and dateBeginningPeriod != daysInMonthBeginning:
        raise ArgumentError("Periodic semi-monthly accrual model requires that the " +
                            "date that would begin the period be on the 15th or " +
                            "final day of the month")

    periods = (date.year - dateBeginningPeriod.year) * 24
    periods += (date.month - dateBeginningPeriod.month) * 2
    if date.day == daysInMonth and dateBeginningPeriod.day == 15:
        periods += 1
    elif date.day == 15 and dateBeginningPeriod.day == daysInMonthBeginning:
        periods -= 1
    return periods / 24

def _portionOfYearPeriodicWeekly(date: date, period: relativedelta):
    fieldsInPeriod = nonZeroValuesInDelta(period)
    if fieldsInPeriod != ['days']:
        raise ArgumentError("Periodic weekly accrual model does not support periods " +
                            "containing non-day values")
    if period.days % 7:
        raise ArgumentError("Periodic weekly accrual model only works for periods " +
                            "that are multiples of 7 days")
    return (period.days // 7) / 52

def _portionOfYearPeriodicBiweekly(date: date, period: relativedelta):
    fieldsInPeriod = nonZeroValuesInDelta(period)
    if fieldsInPeriod != ['days']:
        raise ArgumentError("Periodic biweekly accrual model does not support " +
                            "periods containing non-day values")
    if period.days % 14:
        raise ArgumentError("Periodic weekly accrual model only works for periods " +
                            "that are multiples of 14 days")
    return (period.days // 14) / 26

def _portionOfYearPeriodicYearly(date: date, period: relativedelta):
    fieldsInPeriod = nonZeroValuesInDelta(period)
    if fieldsInPeriod != ['years']:
        raise ArgumentError("Periodic yearly accrual model does not support periods " +
                            "containing non-year values")
    return period.years

def _portionOfYearProRata(date: date, period: relativedelta):
    periodStart = date - period
    days = date.toordinal() - periodStart.toordinal()
    daysInYear = 366 if isleap(date.year) else 365
    return days / daysInYear

def portionOfYear(date: date, period: relativedelta, accrualModel: AccrualModel) -> float:
    if accrualModel == AccrualModel.PeriodicMonthly:
        return _portionOfYearPeriodicMonthly(date, period)
    elif accrualModel == AccrualModel.PeriodicSemiMonthly:
        return _portionOfYearPeriodicSemiMonthly(date, period)
    elif accrualModel == AccrualModel.PeriodicWeekly:
        return _portionOfYearPeriodicWeekly(date, period)
    elif accrualModel == AccrualModel.PeriodicBiweekly:
        return _portionOfYearPeriodicBiweekly(date, period)
    elif accrualModel == AccrualModel.PeriodicYearly:
        return _portionOfYearPeriodicYearly(date, period)
    else: # pro rata
        return _portionOfYearProRata(date, period)

