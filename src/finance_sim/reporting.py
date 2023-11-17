from typing import Tuple
from finance_sim.config import ScenarioConfig, StateType
import finance_sim.main as finSim

from calendar import monthrange
from datetime import date
from dateutil.relativedelta import relativedelta
from pandas import DataFrame

from finance_sim.scheduling import AccrualModel

def _assembleInitialState(config: ScenarioConfig) \
    -> finSim.FinanceState:
    result = finSim.FinanceState(config.time.startingDate)
    for stateConfig in config.initialState:
        if stateConfig.type == StateType.cash:
            result.cash += float(stateConfig.data['value'])
        elif stateConfig.type == StateType.constantGrowthAsset:
            result.constantGrowthAssets.append(
                finSim.ConstantGrowthAsset(
                    accrualModel=config.time.accrualModel,
                    initialValue=stateConfig.data['value'],
                    annualAppreciation=stateConfig.data['appreciation']))
    return result

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

def _synchronizeUpdates(config: ScenarioConfig, eventDate: date, history: finSim.FinanceHistory):
    for scheduledEvent in config.scheduledValues:
        if eventDate >= scheduledEvent.startDate:
            if eventDate < scheduledEvent.endDate and not scheduledEvent.active:
                scheduledState = scheduledEvent.state
                if scheduledState.type == StateType.cash:
                    latestState = history.latestState()
                    latestState.cash += scheduledState.data['value']
                    history.data[-1] = latestState
                elif scheduledState.type == StateType.constantGrowthAsset:
                    latestState = history.latestState()
                    constantGrowthAsset = finSim.ConstantGrowthAsset(
                        accrualModel=config.time.accrualModel,
                        initialValue=scheduledState.data['value'],
                        annualAppreciation=scheduledState.data['appreciation'])
                    latestState.constantGrowthAssets.append(constantGrowthAsset)
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
        eventDate, delta = _nextDate(eventDate, accrualModel)

def report(config: ScenarioConfig) -> DataFrame:
    initialState = _assembleInitialState(config)
    history = finSim.FinanceHistory(initialState)
    _simulate(config, history)
    return DataFrame()
