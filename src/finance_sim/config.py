import yaml
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

@dataclass
class TimeConfig(object):
    granularity: str
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
    schedule: datetime

@dataclass
class ScenarioConfig(object):
    time: TimeConfig
    initialValues: list[StateConfig]
    scheduledValues: list[ScheduledState]

def parseConfig(path: str) -> ScenarioConfig:
    with open(path, 'r') as configFile:
        return yaml.parse(configFile)
