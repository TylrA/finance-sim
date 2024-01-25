import subprocess


def runTests():
    command = "pytest test/*.py"
    subprocess.run(command, shell=True, check=True)


def format():
    command = "black ."
    subprocess.run(command, shell=True, check=True)
