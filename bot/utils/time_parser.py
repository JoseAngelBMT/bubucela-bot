def time_to_seconds(time: str) -> float:
    """
    Convert time string to seconds.
    
    Args:
        time: Time string in format hh:mm:ss, mm:ss or ss
        
    Returns:
        Time in seconds
        
    Raises:
        ValueError: If time format is invalid
    """
    match [int(p) for p in time.strip().split(":")]:
        case [h, m, s]:
            return h * 3600 + m * 60 + s
        case [m, s]:
            return m * 60 + s
        case [s]:
            return s
        case _:
            raise ValueError(f"Time format not valid: {time}")
