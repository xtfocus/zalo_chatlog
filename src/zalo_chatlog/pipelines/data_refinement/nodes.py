import asyncio
import json
import logging
import os
from typing import Dict, List

import aiohttp
from numpy import outer
from pandas import DataFrame, to_datetime
from tqdm import tqdm

from .intent_classification import make_async_request
from .pool_events import get_event

tqdm.pandas()

logger = logging.getLogger(__name__)


def connecting_sessions(chatlog: DataFrame) -> DataFrame:
    """
    Sometimes two sessions are just one conversation broken into multiple sessions,
        maybe due to inactivity or whatever quirks. In such cases, we want to connect
        them. Here's how: a conversation = [senderid + the day]

        E.g., senderid = 1234, datetime is 2024-01-01
        --> daily_session_code = 123420240101

    This approach is not sophisticated enough when the user actually opens multiple sessions
        for unrelated needs. But it should be good enough
    """

    chatlog["daily_session_code"] = chatlog["sender_id"].astype(str) + chatlog[
        "created_time"
    ].str.slice(0, 10).str.replace("-", "")
    chatlog = chatlog.sort_values(["sender_id", "created_time"])
    return chatlog


def create_time_column(chatlog: DataFrame) -> DataFrame:
    """
    Create a column named `time_diff` to measure the time from the start of the conversation
        to the current message row (in minutes, rounded to 2nd decimal digit)
    """

    chatlog["datetime"] = to_datetime(chatlog["created_time"])

    # Calculate the time difference in minutes from each row to the first row within each session
    chatlog["time_diff"] = chatlog.groupby("daily_session_code")[
        "datetime"
    ].progress_transform(lambda x: round((x - x.min()).dt.total_seconds() / 60, 2))

    # Calculate the time difference in minutes from each row to the last row within each session
    chatlog["time_interval"] = chatlog.groupby("daily_session_code")[
        "time_diff"
    ].progress_transform(lambda x: round(x.diff(), 2))

    return chatlog.drop("datetime", axis=1)


def pool_events(chatlog: DataFrame, events: List[str]) -> DataFrame:
    """
    Create a new column named `all_classified`, True if all messages
        are classified, False if at least one message is either
        - cus_text_other; or
        - agent_text_other

    Create an `events` columnn which is a list of events
    """

    # Pool the event into a single column
    chatlog["event"] = chatlog.progress_apply(lambda x: get_event(x, events), axis=1)

    # Grouping event into a list of events
    chatlog["events"] = chatlog.groupby(["daily_session_code"])[
        "event"
    ].progress_transform(lambda x: [x.tolist()] * len(x))

    # If all event are classified, mark as all_classified
    chatlog["all_classified"] = chatlog["events"].progress_apply(
        lambda x: all(
            [(event not in ("cus_text_other", "agent_text_other")) for event in x]
        )
    )
    # Warning when un-defined events exist
    if sum(chatlog["event"].isna()):
        warning = "Exists messages that are not categorized"
        logger.warning(warning)

        logger.warning("Converting them to `nan`")
        # Make convert null events to nan
        chatlog["event"] = chatlog["event"].fillna("nan")

    # Create the string of events by srting concatenation
    chatlog["events"] = chatlog["events"].apply(lambda x: "|".join([str(i) for i in x]))

    return chatlog.drop(events, axis=1)


def categorize_organic_sessions(
    chatlog: DataFrame, organic_requirements: Dict[str, int]
):
    """
    Extract organic sessions via zalo chat.
    organic_requirements is a dict that contains the requirement for a session to be
        considered organic. For instance:
        - at least 2 organic texts from the agent
        - at least 2 organic texts from the customer

    What's an organic text? It has to be a text (meaning not payload/sticker/file), and
        it's not an automated response (e.g., The order confirmation text)

    Specifically, the 'organic' texts has already been labeled as cus_text_other and agent_text_other
    """
    minimum_cus_texts = organic_requirements["customer"]
    minimum_agent_texts = organic_requirements["agent"]

    chatlog["n_org_cus"] = chatlog.groupby(["daily_session_code"])[
        "event"
    ].progress_transform(lambda x: sum(x == "cus_text_other"))

    chatlog["n_org_agent"] = chatlog.groupby(["daily_session_code"])[
        "event"
    ].progress_transform(lambda x: sum(x == "agent_text_other"))

    chatlog["is_organic"] = chatlog.apply(
        lambda x: (x["n_org_cus"] >= minimum_cus_texts)
        & (x["n_org_agent"] >= minimum_agent_texts),
        axis=1,
    )

    chatlog["readable_event"] = chatlog.apply(
        lambda x: (
            json.loads(x["message"])["content"]["text"]
            if x["event"] in ("cus_text_other", "agent_text_other")
            else x["event"]
        ),
        axis=1,
    )

    return chatlog


def export_organic_message_data(chatlog: DataFrame) -> DataFrame:
    """
    Refined organic data for inten-classification inference

    Export the the organic texts only (for now. In the future,
        I can use others texts and other columns as context)
    """

    chatlog = chatlog[chatlog["is_organic"]].reset_index(drop=True)
    # Remove the fillers. For now, keep it simple. In the future, keep a list of this.
    chatlog = chatlog[
        ~chatlog["readable_event"].str.lower().isin(["dạ", "vâng ạ", "dạ vâng ạ"])
    ]
    chatlog = chatlog[chatlog["event"].isin(["cus_text_other", "agent_text_other"])]

    chatlog["sender"] = chatlog.progress_apply(
        lambda x: "Nhân viên nói: " if x["email"] else "Khách hàng nói: ", axis=1
    )
    chatlog["readable_event"] = chatlog["sender"] + chatlog["readable_event"]

    # Maybe it's not the best idea to use df. A txt file would do. For now, make it quick
    result = chatlog[["daily_session_code", "readable_event"]]

    result = (
        result.groupby(["daily_session_code"])["readable_event"]
        .progress_apply(list)
        .reset_index(name="readable_event")
    )

    result["readable_event"] = result["readable_event"].apply(lambda x: "\n".join(x))

    logger.info(f"Example entries\n{result.head(5)}")
    return result


def classify_intent(messages: DataFrame):
    messages = messages.head(250)
    messages_list = list(messages["readable_event"])
    messages_list = [text.strip() for text in messages_list]

    output_file = "data/01_raw/labeled_intent_0101.txt"

    # open empty file
    with open(output_file, "w", encoding="utf-8"):
        pass

    async def make_requests(messages_list):
        async with aiohttp.ClientSession() as session:
            batch_size = 5
            for i in range(0, len(messages_list), batch_size):
                batch = messages_list[i : i + batch_size]
                tasks = [make_async_request(session, text) for text in batch]
                responses = await asyncio.gather(*tasks)
                # Write responses to the output file
                with open(output_file, "a", encoding="utf-8") as file:
                    for response in responses:
                        file.write(response + "\n")

                logger.info(f"Finished {i}-{i+batch_size}")
                logger.info(
                    f"""
                    {batch[-1]} ===> {responses[-1]} 
                    """
                )

    asyncio.run(make_requests(messages_list))

    with open(output_file, "r") as h:
        responses = h.readlines()

    messages["predicted_intent"] = responses

    logger.info(
        f"""Finished intent-classification. Example:
    {messages.sample(10)}"""
    )
    return messages
