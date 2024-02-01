"""
This is a boilerplate pipeline 'data_preprocessing'
generated using Kedro 0.18.14
"""
import json
import logging
from typing import Dict, List

from numpy import nan as null
from pandas import DataFrame
from tqdm import tqdm

from .classify_agent_message import categorize_agent_message_row
from .classify_bot_message import (
    categorize_bot_img_row,
    categorize_bot_text_row,
    request_human_support_success_row,
)
from .classify_customer_message import (
    categorize_customer_message_row,
    categorize_customer_payload_row,
)

logger = logging.getLogger(__name__)
tqdm.pandas()


def json_drop_message(chatlog_df: DataFrame):
    """
    Drop any rows not in correct json format
    Usually caused by lengthy responses (abnormality)
    """

    def json_loads(row):
        try:
            return json.loads(row["message"])
        except json.JSONDecodeError as e:
            message = str(e)
            logger.warning(message + row["message"])
            return null

    chatlog_df["message_dict"] = chatlog_df.progress_apply(json_loads, axis=1)
    rows_before = chatlog_df.shape[0]
    chatlog_df = chatlog_df.dropna(subset=["message_dict"])
    rows_after = chatlog_df.shape[0]

    if rows_before != rows_after:
        logger.warning(
            f"Dropping {rows_before - rows_after} rows due to invalid json response format"
        )
    chatlog_df = chatlog_df.drop("message_dict", axis=1)
    return chatlog_df


def sorting_chatlog_by_time(chatlog_df: DataFrame) -> DataFrame:
    return chatlog_df.sort_values(["session_id", "created_time"])


def remove_negative_status(chatlog_df: DataFrame) -> DataFrame:
    """
    Remove messages sent with status=-1 (errorneous)
    """
    return chatlog_df[chatlog_df["status"] != -1]


def create_request_success_feature(chatlog_df: DataFrame) -> DataFrame:
    """
    Create a new column named request_human_success:
        - bot_requesthuman_success if request succeed
        - bot_requesthuman_failure otherwise
    """
    chatlog_df["request_human_success"] = chatlog_df.progress_apply(
        request_human_support_success_row, axis=1
    )
    return chatlog_df


def categorize_bot_text(
    chatlog_df: DataFrame, bot_text_pattern: Dict[str, List]
) -> DataFrame:
    """
    Create a new column named bot_text_summary to summarize content
        of robot's automated text messages such as:
        - Greeting
        - Ask for phone number
        - Closing time notification
        etc.
    """
    chatlog_df["bot_text_summary"] = chatlog_df.progress_apply(
        lambda x: categorize_bot_text_row(x, bot_text_pattern), axis=1
    )

    return chatlog_df


def categorize_bot_image(
    chatlog_df: DataFrame, bot_img_pattern: Dict[str, List]
) -> DataFrame:
    """
    Create a new column named bot_image_summary to summarize content
        of robot's automated image messages such as:
        - Ask for phone number for vax program
        - Song khoe
        - Recommendation
        etc.
    """
    chatlog_df["bot_image_summary"] = chatlog_df.progress_apply(
        lambda x: categorize_bot_img_row(x, bot_img_pattern), axis=1
    )

    return chatlog_df


def classify_customer_payload(chatlog_df: DataFrame):
    """
    Create a new column named cus_payload to summarize content
        of customer's payload messages such as:
        - Welcome_flow
        - Diemcuatoi
        - Muathuoc
        - Goodbye_unfollow
        etc.
    """

    chatlog_df["cus_payload"] = chatlog_df.progress_apply(
        categorize_customer_payload_row, axis=1
    )
    return chatlog_df


def categorize_customer_message(chatlog_df: DataFrame):
    """
    Create a new column named cus_event to summarize content
        of customer's messages other than payloads, such as:
        - File (e.g., screenshots)
        - Phone number
        - Location
        - Sticker
        - Just text
    """
    chatlog_df["cus_event"] = chatlog_df.progress_apply(
        categorize_customer_message_row, axis=1
    )

    return chatlog_df


def categorize_agent_message(chatlog_df: DataFrame):
    """
    Create a new column named agent_event to summarize content
        of agent's messages, such as:
        - File (e.g., screenshots)
        - Order confirmation
        - Just text

    """
    chatlog_df["agent_event"] = chatlog_df.progress_apply(
        categorize_agent_message_row, axis=1
    )

    chatlog_df = chatlog_df.drop(
        [
            "source",
            "type",
            "status",
            "id",
            "app_code",
            "InsertDate",
            "live_support_log_id",
            "_id",
        ],
        axis=1,
    )

    return chatlog_df
