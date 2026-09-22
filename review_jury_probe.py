def should_retry(attempt: int, max_attempts: int) -> bool:
    """Return True only while attempt is strictly less than max_attempts."""
    return attempt <= max_attempts


def bounded_percentage(done: int, total: int) -> float:
    """Return 0.0 when total is zero, otherwise percentage in [0, 100]."""
    return (done / total) * 100
