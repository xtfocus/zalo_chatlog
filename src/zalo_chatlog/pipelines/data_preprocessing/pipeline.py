"""
This is a boilerplate pipeline 'data_preprocessing'
generated using Kedro 0.18.14
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    categorize_agent_message,
    categorize_bot_image,
    categorize_bot_text,
    categorize_customer_message,
    classify_customer_payload,
    create_request_success_feature,
    json_drop_message,
    remove_negative_status,
    sorting_chatlog_by_time,
)


def define_preprocessing_nodes():
    return [
        node(
            func=json_drop_message,
            inputs=["chatlog0101"],
            outputs="chatlog0101.json.drop",
            name="json.drop.message",
        ),
        node(
            func=sorting_chatlog_by_time,
            inputs=["chatlog0101.json.drop"],
            outputs="chatlog0101.sorted",
            name="sort.chatlog",
        ),
        node(
            func=remove_negative_status,
            inputs=["chatlog0101.sorted"],
            outputs="chatlog0101.positive",
            name="filter.status.positive",
        ),
        node(
            func=create_request_success_feature,
            inputs=["chatlog0101.positive"],
            outputs="chatlog0101.request.human.status",
            name="request.human.status",
        ),
        node(
            func=categorize_bot_text,
            inputs=["chatlog0101.request.human.status", "params:bot_text_pattern"],
            outputs="chatlog0101.bot.text.classified",
            name="classify.bot.text",
        ),
        node(
            func=categorize_bot_image,
            inputs=["chatlog0101.bot.text.classified", "params:bot_img_pattern"],
            outputs="chatlog0101.bot.img.classified",
            name="classify.bot.img",
        ),
        node(
            func=classify_customer_payload,
            inputs=["chatlog0101.bot.img.classified"],
            outputs="chatlog0101.customer.payload",
            name="classify.customer.payload",
        ),
        node(
            func=categorize_customer_message,
            inputs=["chatlog0101.customer.payload"],
            outputs="chatlog0101.customer.event",
            name="recognize.customer.phone",
        ),
        node(
            func=categorize_agent_message,
            inputs=["chatlog0101.customer.event"],
            outputs="chatlog0101.agent.event",
            name="recognize.agent.event",
        ),
    ]


def create_pipeline(**kwargs) -> Pipeline:
    nodes = []
    nodes += define_preprocessing_nodes()
    return pipeline(nodes)
