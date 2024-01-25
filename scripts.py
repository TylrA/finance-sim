import subprocess
import black


def runTests():
    command = "pytest test/*.py"
    subprocess.run(command, shell=True, check=True)


def format():
    black.main(".")
