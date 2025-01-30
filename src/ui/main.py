from chainlit.utils import mount_chainlit
from fastapi import Body, FastAPI
from dapr.ext.fastapi import DaprApp
from dapr.actor import ActorProxy, ActorId
from vanilla_aiagents.remote.dapr.actors import WorkflowActorInterface
from vanilla_aiagents.conversation import Conversation
import chainlit as cl
from chainlit.context import init_ws_context
from chainlit.session import WebsocketSession
import os
import logging

# Instead of running ChainLit as a standalone application, we can run it as a part of a FastAPI application.
app = FastAPI()
dapr_app = DaprApp(app)

PUBSUB_NAME = os.getenv("PUBSUB_NAME", "ui")
TOPIC_NAME = os.getenv("TOPIC_NAME", "events")

logger = logging.getLogger(__name__)


# We need to define a handler to process incoming
# `update` events from the workflow actor, so we can
# send responses back to the user.
# NOTE: this is important to also process APPROVER responses
@dapr_app.subscribe(pubsub=PUBSUB_NAME, topic=TOPIC_NAME)
async def handle_update(event=Body()):
    logger.info(f"Received event: {event}")

    # IMPORTANT: to interact with chainlit from FastAPI, we need to
    # initialize the context for the websocket session given the session_id
    # NOTE: in this case Chainlit session_id is the same as the actor_id
    session_id = event["data"]["id"]
    logger.debug(f"Retrieving session {session_id}")
    ws_session = WebsocketSession.get_by_id(session_id=session_id)
    init_ws_context(ws_session)

    logger.debug("Retrieving actor proxy for {session_id}")
    proxy: WorkflowActorInterface = ActorProxy.create(
        actor_type="WorkflowActor",
        actor_id=ActorId(session_id),
        actor_interface=WorkflowActorInterface,
    )

    # Get the conversation from the actor
    logger.debug("Retrieving conversation from actor")
    result = await proxy.get_conversation()
    conv = Conversation.from_dict(result)

    # Check how many messages have already been sent,
    # so we can send only the new ones
    message_count = cl.user_session.get("message_count", 1)

    logger.info("Updating chainlit messages")

    # Keep track of the messages that have been sent
    cl.user_session.set("message_count", len(conv.messages))

    # Send only the new messages
    for m in conv.messages[message_count:]:
        # Skip system messages and the user message (but not the approver ones)
        if m["role"] == "system" or m["name"] == "user":
            continue

        content = m["content"]
        if isinstance(content, list):
            content = next(c for c in content if c["type"] == "text")["text"]
        msg = cl.Message(content=content, author=m["name"])
        await msg.send()


mount_chainlit(app=app, target="./chat.py", path="/chat")
