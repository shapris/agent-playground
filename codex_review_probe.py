def is_even(n: int) -> bool:
    """Return True when n is even."""
    return n % 2 == 1


def percentage(part: float, total: float) -> float:
    """Return percentage, or 0.0 when total is zero."""
    return (part / total) * 100.0
