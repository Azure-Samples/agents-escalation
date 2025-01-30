from dapr.clients import DaprClient
import chainlit as cl
import os
from dotenv import load_dotenv
from vanilla_aiagents.remote.dapr.actors import InputWorkflowEvent

load_dotenv(override=True)

PUBSUB_NAME = os.getenv("PUBSUB_NAME", "ui")
TOPIC_NAME = os.getenv("TOPIC_NAME", "events")

# Chainlit app, but NOT entrypoint
# Check main.py for entrypoint


@cl.on_chat_start
async def on_chat_start():
    send_message("Hello")


@cl.on_message
async def on_message(msg: cl.Message):
    send_message(msg.content)


def send_message(message: str):
    # NOTE: for simplicity, we are using the user_session id as
    # the conversation and actor id
    id = cl.user_session.get("id")

    # Instead of communicating with the actor directly, we will
    # publish an event to the pubsub, which the actor will listen to
    with DaprClient() as client:
        event = InputWorkflowEvent(
            input=message,
            id=id,
            type="input",
        )
        client.publish_event(
            PUBSUB_NAME,
            TOPIC_NAME,
            data=event.json(),
            data_content_type="application/json",
            publish_metadata=event.metadata(),
        )
