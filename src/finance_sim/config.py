import yaml
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TimeConfig(object):
    granularity: str
    period: int

class StateType:
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
    schedule: datetime

@dataclass
class ScenarioConfig(object):
    time: TimeConfig
    initialValues: list[StateConfig]
    scheduledValues: list[ScheduledState]

def parseConfig(path: str):
    with open(path, 'r') as configFile:
        return yaml.parse(configFile)
