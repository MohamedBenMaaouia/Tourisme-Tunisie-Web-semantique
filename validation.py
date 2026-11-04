"""Validation des paramètres de requête HTTP."""
import re


class ApiError(Exception):
    def __init__(self, status: int, message: str, details=None):
        super().__init__(message)
        self.status = status
        self.message = message
        self.details = details


def get_bool(args, name, default=True):
    raw = args.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in ("true", "1", "oui", "yes"):
        return True
    if value in ("false", "0", "non", "no"):
        return False
    raise ApiError(400, f"Le paramètre '{name}' doit être true ou false.")


def get_int(args, name, default=None, minimum=None, maximum=None):
    raw = args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ApiError(400, f"Le paramètre '{name}' doit être un entier (reçu : '{raw}').")
    _check_bounds(name, value, minimum, maximum)
    return value


def get_float(args, name, default=None, minimum=None, maximum=None):
    raw = args.get(name)
    if raw is None or raw == "":
        return default
    try:
        value = float(raw)
    except ValueError:
        raise ApiError(400, f"Le paramètre '{name}' doit être un nombre (reçu : '{raw}').")
    _check_bounds(name, value, minimum, maximum)
    return value


def get_choice(args, name, choices):
    raw = args.get(name)
    if raw is None or raw == "":
        return None
    value = raw.strip().lower()
    if value not in choices:
        raise ApiError(400, f"Valeur invalide pour '{name}' : '{raw}'.",
                       {"valeurs_autorisees": sorted(choices)})
    return value


def get_pattern(args, name, pattern, hint):
    raw = args.get(name)
    if raw is None or raw == "":
        return None
    value = raw.strip().lower()
    if not re.fullmatch(pattern, value):
        raise ApiError(400, f"Format invalide pour '{name}' : {hint}.")
    return value


def _check_bounds(name, value, minimum, maximum):
    if minimum is not None and value < minimum:
        raise ApiError(400, f"Le paramètre '{name}' doit être >= {minimum}.")
    if maximum is not None and value > maximum:
        raise ApiError(400, f"Le paramètre '{name}' doit être <= {maximum}.")
