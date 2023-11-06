import pytest
from finance_sim import *

def testParseConfig():
    path = 'examples/finance-config.yaml'
    parseConfig(path)
