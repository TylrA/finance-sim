from ctypes import ArgumentError
import re
import os

from .scheduling import AccrualModel


def parseAccrualModel(accrualModelStr: str) -> AccrualModel:
    pattern = r"(pro rata|periodic (?:monthly|semi ?monthly|weekly|biweekly|yearly))"
    match = re.match(pattern, accrualModelStr)
    if not match:
        raise ArgumentError(
            "accrualModelStr must match the regex pattern {}, got {}".format(
                pattern, accrualModelStr
            )
        )

    if accrualModelStr == "pro rata":
        return AccrualModel.ProRata
    if accrualModelStr == "periodic monthly":
        return AccrualModel.PeriodicMonthly
    if (
        accrualModelStr == "periodic semi monthly"
        or accrualModelStr == "periodic semimonthly"
    ):
        return AccrualModel.PeriodicSemiMonthly
    if accrualModelStr == "periodic weekly":
        return AccrualModel.PeriodicWeekly
    if accrualModelStr == "periodic biweekly":
        return AccrualModel.PeriodicBiweekly
    if accrualModelStr == "periodic yearly":
        return AccrualModel.PeriodicYearly

    raise RuntimeError("None of the supported accrual model was used")


def getEnvVar(variable: str) -> str:
    return os.getenv(variable) or ""
