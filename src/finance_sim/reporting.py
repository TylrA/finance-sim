from typing import Any, Tuple

import numpy as np
from calendar import monthrange
from datetime import date
from dateutil.relativedelta import relativedelta
from pandas import DataFrame

from .config import ScenarioConfig, StateType, parseConfig
from .main import \
    EventGroup, \
    AbstractEvent, \
    ConstantGrowthAsset, \
    FinanceHistory, \
    addToCash, \
    abstractEventType
from .scheduling import AccrualModel

def _assembleInitialState(config: ScenarioConfig) \
    -> EventGroup:
    events: dict[str, AbstractEvent] = {}
    for stateConfig in config.initialState:
        if stateConfig.type in abstractEventType:
            events[stateConfig.name] = \
                abstractEventType[stateConfig.type](stateConfig.data,
                                                    stateConfig.name)
        else:
            raise RuntimeError('{} is not a valid event type'.format(stateConfig.type))
    return EventGroup(config.time.startingDate, events)

def _nextDate(eventDate: date, accrualModel: AccrualModel) -> Tuple[date, relativedelta]:
    if accrualModel == AccrualModel.PeriodicMonthly:
        delta = relativedelta(months=1)
        return eventDate + delta, delta
    elif accrualModel == AccrualModel.PeriodicSemiMonthly:
        if eventDate.day == 15:
            delta = relativedelta(
                days = monthrange(eventDate.year, eventDate.month)[1] - 15)
        else:
            delta = relativedelta(days=15)
        return eventDate + delta, delta
    elif accrualModel == AccrualModel.PeriodicWeekly:
        delta = relativedelta(days=7)
        return eventDate + delta, delta
    elif accrualModel == AccrualModel.PeriodicBiweekly:
        delta = relativedelta(days=14)
        return eventDate + delta, delta
    elif accrualModel == AccrualModel.PeriodicYearly:
        delta = relativedelta(years=1)
        return eventDate + delta, delta
    return date(2000, 1, 1), relativedelta(months=0)

def _synchronizeUpdates(config: ScenarioConfig,
                        eventDate: date,
                        history: FinanceHistory):
    for scheduledEvent in config.scheduledValues:
        if eventDate >= scheduledEvent.startDate:
            if eventDate < scheduledEvent.endDate and not scheduledEvent.active:
                scheduledState = scheduledEvent.state
                if scheduledState.type in abstractEventType:
                    latestEvents = history.latestEvents()
                    latestEvents.events[scheduledState.name] = \
                        abstractEventType[scheduledState.type](
                            scheduledState.data,
                            scheduledState.name)
                    scheduledEvent.active = True
                # else:
                #     raise RuntimeError('{} is not a valid event type'.format(
                #         scheduledState.type))
                # if scheduledState.type == StateType.cash:
                #     latestEvents = history.latestEvents()
                #     addToCash(latestEvents, scheduledState.data['value'])
                # elif scheduledState.type == StateType.constantGrowthAsset:
                #     latestEvents = history.latestEvents()
                #     constantGrowthAsset = ConstantGrowthAsset(
                #         None,
                #         scheduledState.name,
                #         accrualModel=config.time.accrualModel,
                #         initialValue=scheduledState.data['value'],
                #         annualAppreciation=scheduledState.data['appreciation'])
                #     latestEvents.events[scheduledState.name] = constantGrowthAsset
                # scheduledEvent.active = True
            elif eventDate >= scheduledEvent.endDate and scheduledEvent.active:
                scheduledState = scheduledEvent.state
                latestEvents = history.latestEvents()
                del latestEvents.events[scheduledState.name] # todo: see below todo
                scheduledEvent.active = False

def _simulate(config: ScenarioConfig, history: FinanceHistory):
    accrualModel = config.time.accrualModel
    eventDate, delta = _nextDate(config.time.startingDate, accrualModel)
    while eventDate < (config.time.startingDate + relativedelta(years=config.time.period)):
        history.passEvent(eventDate, delta) # todo: split passEvent into 2 parts so we can delete the pending event, rather than the previous event
        _synchronizeUpdates(config, eventDate, history)
        eventDate, delta = _nextDate(eventDate, accrualModel)

def _stateToRow(state: EventGroup) -> list:
    result: list[Any] = [state.date]
    result.extend([str(event) for _, event in state.events.items()])
    return result

def report(config: ScenarioConfig) -> DataFrame:
    initialEvents = _assembleInitialState(config)
    history = FinanceHistory(initialEvents)
    _simulate(config, history)
    return DataFrame([_stateToRow(d) for d in history.data])

if __name__ == '__main__':
    config = parseConfig('../../examples/finance-config.yaml')
    print(report(config).to_csv())
