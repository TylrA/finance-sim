# from typing import (functions)

class FinanceData(object):
    def __init__(self, cash = 0):
        self.cash = [cash]
    
    def appendEvent(self, cash = 0, **kwargs):
        self.cash.append(cash)

# todo: create a list of functions (events) that will be called (happen) once every time period according to the granularity.
# an "event" will possibly append a state to the FinanceData object (more/less cash, etc.)

if __name__ == '__main__':
    
    pass
