import logging
from typing import List

from numpy import nan as null

logger = logging.getLogger(__name__)


def get_event(row, events: List[str]):
    """
    Make sure the row contains no more than one event. If this is violated,
        raise error

    If no event detected, raise warning and return null
    If a single detected, return that event
    """
    event = []
    for column in events:
        if row[column]:
            event.append(row[column])
        if len(event) > 1:
            logger.info(row["session_id"])

    try:
        assert len(event) <= 1
    except AssertionError as e:
        message = f"More than one event detected for {row['session_id']}, consider reviewing patterns or event definition"
        logger.error(message)
        raise ValueError(message) from e

    if event:
        return event[0]
    else:
        logger.warning("No event detected for row['message]")
        return null
