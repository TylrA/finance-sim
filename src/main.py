# from typing import (functions)
import sys

class FinanceData(object):
    def __init__(self, cash = 0):
        self.cash = [cash]
    
    def appendEvent(self, cash = 0, **kwargs):
        self.cash.append(cash)

# todo: create a list of functions (events) that will be called (happen) once every time period according to the granularity.
# an "event" will possibly append a state to the FinanceData object (more/less cash, etc.)
financeEvents = []

if __name__ == '__main__':
    if len(sys.argv) <= 2:
        print("Usage: {} <granularity> <time-period>".format(sys.argv[0]))
        print()
        print("   granularity  number of events in a year (e.g. 12 for monthly)")
        print("   time-period  number of years to calculate")
        exit(1)

    granularity = sys.argv[1]
    timePeriod = sys.argv[2]

    if not granularity.isnumeric():
        print("granularity must be numeric, got {}".format(granularity))
        exit(1)
    if not timePeriod.isnumeric():
        print("time-period must be numeric, got {}".format(timePeriod))
        exit(1)
    pass
