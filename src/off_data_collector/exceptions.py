"""
Exceptions module.
"""


class OFFDCError(Exception):
    """
    Base class for all exceptions thrown by the off_data_collector module.
    """


class InvalidUnitError(OFFDCError):
    """
    Thrown when a quantity unit is invalid or unknown.
    """
