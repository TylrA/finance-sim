import yaml

def parseConfig(path: str):
    with open(path, 'r') as configFile:
        return yaml.parse(configFile)
