from ctypes import ArgumentError
import re
import yaml
from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta
from enum import Enum

from finance_sim.scheduling import AccrualModel, nonZeroValuesInDelta

@dataclass
class TimeConfig(object):
    granularity: relativedelta
    accrualModel: AccrualModel
    period: int
    startingDate: date

class StateType(Enum):
    cash = 1
    constantGrowthAsset = 2

@dataclass
class StateConfig(object):
    type: StateType
    value: float
    name: str

@dataclass
class ScheduledState(object):
    state: StateConfig
    schedule: date

@dataclass
class ScenarioConfig(object):
    time: TimeConfig
    initialState: list[StateConfig]
    scheduledValues: list[ScheduledState]

def parseGranularity(granularityStr: str) -> relativedelta:
    pattern = r'(\d+)\s*(d|w|M2?|Y)'
    match = re.match(pattern, granularityStr)
    if not match:
        raise ArgumentError('granularityStr must match the regex pattern {}, got {}'
                            .format(pattern, granularityStr))

    groups = match.groups()
    value = int(groups[1])
    unit = groups[2]
    if unit == 'd':
        return relativedelta(days = value)
    if unit == 'w':
        return relativedelta(days = 7 * value)
    if unit == 'M':
        return relativedelta(months = value)
    if unit == 'M2':
        return relativedelta(days = 15 * value)
    if unit == 'Y':
        return relativedelta(years = value)

    raise RuntimeError('None of the supported units was used')

def parseAccrualModel(accrualModelStr: str) -> AccrualModel:
    pattern = r'(pro rata|periodic (?:monthly|semi ?monthly|weekly|biweekly|yearly))'
    match = re.match(pattern, accrualModelStr)
    if not match:
        raise ArgumentError('accrualModelStr must match the regex pattern {}, got {}'
                            .format(pattern, accrualModelStr))

    if accrualModelStr == 'pro rata':
        return AccrualModel.ProRata
    if accrualModelStr == 'periodic monthly':
        return AccrualModel.PeriodicMonthly
    if accrualModelStr == 'periodic semi monthly' or \
       accrualModelStr == 'periodic semimonthly':
        return AccrualModel.PeriodicSemiMonthly
    if accrualModelStr == 'periodic weekly':
        return AccrualModel.PeriodicWeekly
    if accrualModelStr == 'periodic biweekly':
        return AccrualModel.PeriodicBiweekly
    if accrualModelStr == 'periodic yearly':
        return AccrualModel.PeriodicYearly

    raise RuntimeError('None of the supported accrual model was used')

def parseStateConfig(rawStateConfig) -> list[StateConfig]:
    values = []
    for state in rawStateConfig['values']:
        if state['type'] == 'cash':
            stateType = StateType.cash
        elif state['type'] == 'constant-growth-asset':
            stateType = StateType.constantGrowthAsset
        else:
            raise RuntimeError('state type only supports "cash" and ' +
                               '"constant-growth-asset"')

        values.append(StateConfig(type=stateType,
                                  value=state['value'],
                                  name=state['name']))
    return values

def parseScheduledStateUpdates(rawScheduledUpdates) -> list[ScheduledState]:
    pass

def parseConfig(path: str) -> ScenarioConfig:
    with open(path, 'r') as configFile:
        rawConfig = yaml.parse(configFile)
        if 'time' not in rawConfig:
            raise RuntimeError('Configuration requires a "time" field')
        if 'initialState' not in rawConfig:
            raise RuntimeError('Configuration requires an "initialState" field')
        rawTimeConfig = rawConfig['time']
        if 'period' not in rawTimeConfig and \
           'granularity' not in rawTimeConfig and \
           'accrualModel' not in rawTimeConfig:
            raise RuntimeError('"time" field requires "granularity", "accrualModel", ' +
                               'and "period"')
        timeConfig = TimeConfig(
            granularity=parseGranularity(rawTimeConfig['granularity']),
            accrualModel=parseAccrualModel(rawTimeConfig['accrualModel']),
            period=int(rawTimeConfig['period']),
            date=date.fromisoformat(rawTimeConfig['startingDate']))

        if 'initialState' not in rawConfig:
            raise RuntimeError('Configuration requires an "initialState" field')

        stateConfig = parseStateConfig(rawConfig['initialState'])

        if 'scheduledStateUpdates' not in rawConfig:
            raise RuntimeError('Configuration requires a "scheduledStateUpdates" field')

        scheduledUpdates = parseScheduledStateUpdates(rawConfig['scheduledStateUpdates'])

        return ScenarioConfig(time = timeConfig,
                              initialState = stateConfig,
                              scheduledValues = scheduledUpdates)
