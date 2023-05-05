__all__ = ("truncate",)


def truncate(text: str, *, length: int) -> str:
    """Truncate a string to a certain length.

    Parameters
    ----------
    text:
        The string to truncate.
    length:
        The length to truncate to.

    Returns
    -------
    str
        The truncated string.
    """
    if len(text) > length:
        return text[: length - 3] + "..."
    return text
