def time_to_seconds(time: str) -> float:
    """Convert a time string to seconds.

    Accepted formats: ``hh:mm:ss``, ``mm:ss`` or ``ss``.
    Decimal fractions are allowed in the last component, e.g. ``1:02.5`` or ``0.25``.
    """
    raw = time.strip()
    if not raw:
        raise ValueError("Time format not valid: empty value")

    parts = raw.split(":")

    total = 0.0
    try:
        match len(parts):
            case 3:
                h = int(parts[0])
                m = int(parts[1])
                s = float(parts[2])
                total = h * 3600 + m * 60 + s
            case 2:
                m = int(parts[0])
                s = float(parts[1])
                total = m * 60 + s
            case 1:
                total = float(parts[0])
            case _:
                raise ValueError
    except ValueError as exc:
        raise ValueError(f"Time format not valid: {time}") from exc

    if total < 0:
        raise ValueError(f"Time format not valid: {time}")

    return total

