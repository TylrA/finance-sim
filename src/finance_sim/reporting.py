from finance_sim.config import ScenarioConfig, StateType
import finance_sim.main as finSim

from datetime import date
from pandas import DataFrame

def assembleInitialState(config: ScenarioConfig) \
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

def report(config: ScenarioConfig) -> DataFrame:
    initialState = assembleInitialState(config)
    history = finSim.FinanceHistory(initialState)
    return DataFrame()
