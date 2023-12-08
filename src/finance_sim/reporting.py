from typing import Any, Tuple

import numpy as np
from finance_sim.config import ScenarioConfig, StateType, parseConfig
import finance_sim.main as finSim

from calendar import monthrange
from datetime import date
from dateutil.relativedelta import relativedelta
from pandas import DataFrame

from finance_sim.scheduling import AccrualModel

def _assembleInitialState(config: ScenarioConfig) \
    -> finSim.EventGroup:
    # result = finSim.FinanceState(config.time.startingDate)
    events: dict[str, finSim.AbstractEvent] = {}
    for stateConfig in config.initialState:
        if stateConfig.type == StateType.cash:
            events[stateConfig.name] = finSim.CashEvent(stateConfig.name,
                                                        stateConfig.data['value'])
        elif stateConfig.type == StateType.constantGrowthAsset:
            events[stateConfig.name] = \
                finSim.ConstantGrowthAsset(stateConfig.name,
                                           config.time.accrualModel,
                                           stateConfig.data['value'],
                                           stateConfig.data['appreciation'])
    return finSim.EventGroup(config.time.startingDate, events)

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
                        history: finSim.FinanceHistory):
    for scheduledEvent in config.scheduledValues:
        if eventDate >= scheduledEvent.startDate:
            if eventDate < scheduledEvent.endDate and not scheduledEvent.active:
                scheduledState = scheduledEvent.state
                if scheduledState.type == StateType.cash:
                    latestEvents = history.latestEvents()
                    finSim.addToCash(latestEvents, scheduledState.data['value'])
                elif scheduledState.type == StateType.constantGrowthAsset:
                    latestEvents = history.latestEvents()
                    constantGrowthAsset = finSim.ConstantGrowthAsset(
                        scheduledState.name,
                        accrualModel=config.time.accrualModel,
                        initialValue=scheduledState.data['value'],
                        annualAppreciation=scheduledState.data['appreciation'])
                    latestEvents.events[scheduledState.name] = constantGrowthAsset
                scheduledEvent.active = True
            elif eventDate >= scheduledEvent.endDate and scheduledEvent.active:
                scheduledState = scheduledEvent.state
                if scheduledState.type == StateType.cash:
                    delta = relativedelta(years=config.time.period)
                    eventEndDate = config.time.startingDate + delta
                    raise RuntimeError("scheduled cash events should not end before the " +
                                       "period ends.\nEvent date: {}\n".format(eventDate) +
                                       "Period end date: {}".format(eventEndDate))
                elif scheduledState.type == StateType.constantGrowthAsset:
                    delta = relativedelta(years=config.time.period)
                    eventEndDate = config.time.startingDate + delta
                    raise RuntimeError("scheduled events of the type constant growth " +
                                       "asset should not end before the period ends.\n" +
                                       "Event date: {}\n".format(eventDate) +
                                       "Period end date: {}".format(eventEndDate))
                scheduledEvent.active = False

def _simulate(config: ScenarioConfig, history: finSim.FinanceHistory):
    accrualModel = config.time.accrualModel
    eventDate, delta = _nextDate(config.time.startingDate, accrualModel)
    while eventDate < (config.time.startingDate + relativedelta(years=config.time.period)):
        history.passEvent(eventDate, delta)
        _synchronizeUpdates(config, eventDate, history)
        eventDate, delta = _nextDate(eventDate, accrualModel)

def _stateToRow(state: finSim.EventGroup) -> list:
    result: list[Any] = [state.date]
    result.extend([str(event) for _, event in state.events.items()])
    return result

def report(config: ScenarioConfig) -> DataFrame:
    initialEvents = _assembleInitialState(config)
    history = finSim.FinanceHistory(initialEvents)
    # history.setEventComponents(finSim.balanceComponents(history))
    _simulate(config, history)
    return DataFrame([_stateToRow(d) for d in history.data])

if __name__ == '__main__':
    config = parseConfig('../../examples/finance-config.yaml')
    print(report(config).to_csv())
