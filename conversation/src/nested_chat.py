import os
import warnings
from autogen import ConversableAgent, UserProxyAgent, GroupChat, GroupChatManager, AssistantAgent
from dotenv import load_dotenv
import pprint

warnings.filterwarnings("ignore", category=UserWarning, message=".*FLAML.*")

load_dotenv()

"""
This script implements a nested chat framework using the autogen library, which facilitates interactions between multiple agents, including a writer and a critic. 

Key Components:
1. **AssistantAgent (Writer)**: This agent is designed to generate engaging product reviews by transforming technical details into compelling narratives. It is programmed to improve the quality of content based on user feedback.

2. **UserProxyAgent**: This agent simulates user interactions. It operates in a mode where it never requires human input and can terminate the conversation based on specific content cues. It also has configurations for executing code in a specified working directory.

3. **AssistantAgent (Critic)**: This agent acts as a critic, tasked with reviewing the content generated by the writer. It ensures that the content adheres to standards and guidelines, checking for harmful elements or regulatory violations.

The script sets up a collaborative environment where the writer creates content, the user proxy simulates user input, and the critic evaluates the output, ensuring a high-quality final product.
"""


model = "gpt-3.5-turbo"
llm_config = {
    "model": model,
    "temperature": 0.7,
    "api_key": os.getenv("OPENAI_API_KEY"),
    "config_list": [{
        "model": model,
        "api_key": os.getenv("OPENAI_API_KEY"),
        "timeout": 60,
        "max_retries": 3
    }]
}

if not llm_config["api_key"]:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")



writer = AssistantAgent(
    name="Writer",
    llm_config=llm_config,
    system_message="""
    You are a professional writer, known for your insightful and engaging product reviews.
    You transform technical details into compelling narratives.
    You should improve the quality of the content based on the feedback from the user.
    """,
)


user_proxy = UserProxyAgent(
    name="User",
    human_input_mode="NEVER",
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    code_execution_config={
        "last_n_messages": 1,
        "work_dir": "my_code",
        "use_docker": False,
    },
)


critic = AssistantAgent(
    name="Critic",
    llm_config=llm_config,
    system_message="""
    You are a critic, known for your thoroughness and commitment to standards.
    Your task is to scrutinize content for any harmful elements or regulatory violations, ensuring
    all materials align with required guidelines.
    """,
)


def reflection_message(recipient, messages, sender, config):
    print("Reflecting...")
    return f"Reflect and provide critique on the following review. \n\n {recipient.chat_messages_for_summary(sender)[-1]['content']}"



user_proxy.register_nested_chats(
    [
        {
            "recipient": critic,
            "message": reflection_message,
            "summary_method": "last_msg",
            "max_turns": 1,
        }
    ],
    trigger=writer,
)

task = """Write a detailed and engaging product review for the new Meta VR headset."""

res = user_proxy.initiate_chat(
    recipient=writer, message=task, max_turns=2, summary_method="last_msg"
)