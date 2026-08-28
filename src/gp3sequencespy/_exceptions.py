class GP3SequencesError(Exception):
    """Base exception for gp3sequencespy."""


class ValidationError(GP3SequencesError, ValueError):
    """Raised when an input violates a sequence-data or analysis contract."""


class ModelFitError(GP3SequencesError, RuntimeError):
    """Raised when a model cannot be fitted under its declared contract."""


class ParityError(GP3SequencesError, AssertionError):
    """Raised when an R/Python parity assertion fails."""
