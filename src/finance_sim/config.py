import yaml
from dataclasses import dataclass
from datetime import date
from enum import Enum

@dataclass
class TimeConfig(object):
    granularity: date
    period: int

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
    initialValues: list[StateConfig]
    scheduledValues: list[ScheduledState]

def parseConfig(path: str) -> ScenarioConfig:
    with open(path, 'r') as configFile:
        rawConfig = yaml.parse(configFile)
        if 'time' not in rawConfig:
            raise RuntimeError('Configuration requires a "time" field')
        if 'initialState' not in rawConfig:
            raise RuntimeError('Configuration requires an "initialState" field')
        rawTimeConfig = rawConfig['time']
        if 'granularity' not in rawTimeConfig or 'period' not in rawTimeConfig:
            raise RuntimeError('"time" field requires "granularity" and "period"')
        timeConfig = TimeConfig(
            granularity=date.fromisoformat(rawTimeConfig['granularity']),
            period=int(rawTimeConfig['period']))
