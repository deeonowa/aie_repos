
SEVERITY_LABELS = ("low", "medium", "high")


def cvss_to_severity(
    score: float,
    medium_min: float = 4.0,
    high_min: float = 7.0,
) -> tuple[str, int]:
    """Map CVSS v3 base score to low / medium / high (0 / 1 / 2)."""
    if score < medium_min:
        return "low", 0
    if score < high_min:
        return "medium", 1
    return "high", 2
