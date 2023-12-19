from ctypes import ArgumentError
import re
import yaml
from dataclasses import dataclass
from datetime import date
from dateutil.relativedelta import relativedelta
from enum import Enum
from typing import Any

from .scheduling import AccrualModel
from .util import parseAccrualModel

@dataclass
class TimeConfig(object):
    granularity: relativedelta
    accrualModel: AccrualModel
    period: int
    startingDate: date

@dataclass
class StateConfig(object):
    type: str
    name: str
    data: dict[str, Any]

@dataclass
class ScheduledState(object):
    state: StateConfig
    startDate: date
    endDate: date
    active: bool

@dataclass
class ScenarioConfig(object):
    time: TimeConfig
    initialState: list[StateConfig]
    scheduledValues: list[ScheduledState]

def _parseGranularity(granularityStr: str) -> relativedelta:
    pattern = r'(\d+)\s*(d|w|M2?|Y)'
    match = re.match(pattern, granularityStr)
    if not match:
        raise ArgumentError('granularityStr must match the regex pattern {}, got {}'
                            .format(pattern, granularityStr))

    groups = match.groups()
    value = int(groups[0])
    unit = groups[1]
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

def _parseState(stateConfig) -> StateConfig:
    stateType = stateConfig['type']

    return StateConfig(type=stateType,
                       data=stateConfig['data'],
                       name=stateConfig['name'])

def _parseStateConfig(rawStateConfig) -> list[StateConfig]:
    return [_parseState(state) for state in rawStateConfig['values']]

def _parseScheduledStateUpdates(rawScheduledUpdates) -> list[ScheduledState]:
    result: list[ScheduledState] = []
    for scheduledUpdate in rawScheduledUpdates:
        startDate = scheduledUpdate['schedule']['startDate']
        endDate = scheduledUpdate['schedule']['endDate']
        result.append(ScheduledState(startDate=startDate,
                                     endDate=endDate,
                                     state=_parseState(scheduledUpdate['value']),
                                     active=False))
    return result

def parseConfig(path: str) -> ScenarioConfig:
    with open(path, 'r') as configFile:
        rawConfig = yaml.safe_load(configFile)
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
            granularity=_parseGranularity(rawTimeConfig['granularity']),
            accrualModel=parseAccrualModel(rawTimeConfig['accrualModel']),
            period=int(rawTimeConfig['period']),
            startingDate=rawTimeConfig['startingDate'])

        if 'initialState' not in rawConfig:
            raise RuntimeError('Configuration requires an "initialState" field')

        stateConfig = _parseStateConfig(rawConfig['initialState'])

        if 'scheduledStateUpdates' not in rawConfig:
            raise RuntimeError('Configuration requires a "scheduledStateUpdates" field')

        scheduledUpdates = _parseScheduledStateUpdates(rawConfig['scheduledStateUpdates'])

        return ScenarioConfig(time = timeConfig,
                              initialState = stateConfig,
                              scheduledValues = scheduledUpdates)
