from typing import Annotated
from vanilla_aiagents.agent import Agent
from vanilla_aiagents.user import User
from vanilla_aiagents.team import Team
from vanilla_aiagents.llm import AzureOpenAILLM
import os
from dotenv import load_dotenv

load_dotenv(override=True)

llm = AzureOpenAILLM(
    {
        "azure_deployment": os.getenv("AZURE_OPENAI_MODEL"),
        "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
        "api_key": os.getenv("AZURE_OPENAI_KEY"),
        "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
    }
)

# This is the consumer user, chatting with the AI team
enduser = User(
    id="end_user",
    description="A human user, the customer, interacting with the AI team",
    mode="unattended",
)
# This is the approver user, that can be involved by AI team
# to escalate requests and get approvals
approver = User(
    id="approver_user",
    description="A human user that can be involved by AI team to escalate requests and get approvals",
    mode="unattended",
)
# This is the AI agent that processes user inquiries and provides responses
agent = Agent(
    id="agent",
    description="An AI agent that processed user inquiries and provides responses.",
    system_message="""
    You are part of an AI customer service team.
    Your tasks are:
    - Handle item returns, exchanges, and refunds.
    
    # RULES
    - Always behave kindly and professionally.
    - If you don't know the answer, apologize and escalate to the approver.
    - Always ask for the order number.
    - Always ask for the reason for the return.
    - When you have the order number, check for eligibility via tool call
    - If the user is eligible, provide the appropriate instructions.
    - If not eligible, kindly inform the user.
    - If the user complains about the decision, escalate to the approver.
    - If approver answer is Approve, provide the appropriate instructions to the user
    - If approver answer is Decline, kindly inform the user.
            
    BE SURE TO READ INSTRUCTIONS ABOVE CAREFULLY
    """,
    llm=llm,
)


# Basic tool to check if the user is eligible for a return, exchange, or refund
@agent.register_tool(description="check_elibigility")
def check_eligibility(
    order_number: Annotated[str, "The user order number"],
    request_type: Annotated[str, "Kind of user request, from REFUND, EXCHANGE, RETURN"],
) -> Annotated[str, "The eligibility status"]:
    if request_type == "REFUND":
        return "Not Eligible"
    elif request_type == "EXCHANGE":
        return "Eligible"
    elif request_type == "RETURN":
        return "Eligible"
    else:
        return "Request not recognized"


# This will be Actor entry point
# picked by Vanilla AI Agents `run_actors` module
_actor_askable = Team(
    id="team",
    description="",
    llm=llm,
    members=[enduser, approver, agent],
    stop_callback=lambda conversation: False,
)
