from typing import Any, Tuple

from calendar import monthrange
from datetime import date
from dateutil.relativedelta import relativedelta
from pandas import DataFrame

from .config import ScenarioConfig, parseConfig
from .events import (
    EventProfileGroup,
    AbstractEventProfile,
    FinanceHistory,
    abstractEventProfileType,
)
from .scheduling import AccrualModel


def _assembleInitialState(config: ScenarioConfig) -> EventProfileGroup:
    events: dict[str, AbstractEventProfile] = {}
    for stateConfig in config.initialState:
        if stateConfig.type in abstractEventProfileType:
            events[stateConfig.name] = abstractEventProfileType[stateConfig.type](
                stateConfig.data, stateConfig.name
            )
        else:
            raise RuntimeError("{} is not a valid event type".format(stateConfig.type))
    return EventProfileGroup(config.time.startingDate, events)


def _nextDate(eventDate: date, accrualModel: AccrualModel) -> Tuple[date, relativedelta]:
    if accrualModel == AccrualModel.PeriodicMonthly:
        delta = relativedelta(months=1)
        return eventDate + delta, delta
    elif accrualModel == AccrualModel.PeriodicSemiMonthly:
        if eventDate.day == 15:
            delta = relativedelta(days=monthrange(eventDate.year, eventDate.month)[1] - 15)
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


def _synchronizeUpdates(config: ScenarioConfig, eventDate: date, history: FinanceHistory):
    for scheduledEvent in config.scheduledValues:
        if eventDate >= scheduledEvent.startDate:
            if eventDate < scheduledEvent.endDate and not scheduledEvent.active:
                scheduledState = scheduledEvent.state
                if scheduledState.type in abstractEventProfileType:
                    pendingEvents = history.pendingEvents
                    pendingEvents.events[scheduledState.name] = abstractEventProfileType[
                        scheduledState.type
                    ](scheduledState.data, scheduledState.name)
                    scheduledEvent.active = True
            elif eventDate >= scheduledEvent.endDate and scheduledEvent.active:
                scheduledState = scheduledEvent.state
                pendingEvents = history.pendingEvents
                del pendingEvents.events[scheduledState.name]
                scheduledEvent.active = False


def _simulate(config: ScenarioConfig, history: FinanceHistory):
    accrualModel = config.time.accrualModel
    eventDate, delta = _nextDate(config.time.startingDate, accrualModel)
    while eventDate < (config.time.startingDate + relativedelta(years=config.time.period)):
        history._startPendingEventProfile(eventDate)
        _synchronizeUpdates(config, eventDate, history)
        history._processAndPushPending(eventDate, delta)
        eventDate, delta = _nextDate(eventDate, accrualModel)


def _stateToRow(state: EventProfileGroup) -> list:
    result: list[Any] = [state.date]
    result.extend([str(event) for _, event in state.events.items()])
    return result


def report(config: ScenarioConfig) -> DataFrame:
    initialEvents = _assembleInitialState(config)
    history = FinanceHistory(initialEvents)
    _simulate(config, history)
    return DataFrame([_stateToRow(d) for d in history.data])


if __name__ == "__main__":
    config = parseConfig("../../examples/finance-config.yaml")
    print(report(config).to_csv())
