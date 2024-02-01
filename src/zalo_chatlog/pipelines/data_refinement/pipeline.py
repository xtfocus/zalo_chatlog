"""
This is a boilerplate pipeline 'data_separation'
generated using Kedro 0.18.14
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import (
    categorize_organic_sessions,
    classify_intent,
    connecting_sessions,
    create_time_column,
    export_organic_message_data,
    pool_events,
)


def define_separation_nodes():
    return [
        node(
            func=connecting_sessions,
            inputs=["chatlog0101.agent.event"],
            outputs="chatlog0101.connected.session",
            name="connect.session",
        ),
        node(
            func=create_time_column,
            inputs=["chatlog0101.connected.session"],
            outputs="chatlog0101.time.feature",
            name="create.time.feature",
        ),
        node(
            func=pool_events,
            inputs=["chatlog0101.time.feature", "params:event_columns"],
            outputs="chatlog0101.pool.events",
            name="pool.events",
        ),
        node(
            func=categorize_organic_sessions,
            inputs=["chatlog0101.pool.events", "params:organic_requirements"],
            outputs="chatlog0101.organic.session",
            name="organic.session",
        ),
        node(
            func=export_organic_message_data,
            inputs=["chatlog0101.organic.session"],
            outputs="chatlog0101.organic.refined",
            name="refined.organic.messages",
        ),
        node(
            func=classify_intent,
            inputs=["chatlog0101.organic.refined"],
            outputs="chatlog0101.organic.intent",
            name="intent.organic.messages",
        ),
    ]


def create_pipeline(**kwargs) -> Pipeline:
    nodes = []
    nodes += define_separation_nodes()
    return pipeline(nodes)
