from datetime import UTC, date, datetime, timedelta


def utc_now() -> datetime:
    """Current UTC time at millisecond precision, matching what MongoDB stores."""
    now = datetime.now(UTC)
    return now.replace(microsecond=now.microsecond // 1000 * 1000)


def latest_allowed_date() -> date:
    """The latest calendar date anywhere on Earth right now (UTC+14), so a user's "today" is
    never rejected as being in the future, whatever their time zone."""
    return (datetime.now(UTC) + timedelta(hours=14)).date()


def validate_not_future(value: date | None) -> date | None:
    """Pydantic validator: reject calendar dates in the future."""
    if value is not None and value > latest_allowed_date():
        raise ValueError("date cannot be in the future")
    return value
