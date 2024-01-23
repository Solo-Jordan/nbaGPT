from settings import logging, CONFIG_LIST, DB
import autogen
from autogen.agentchat.contrib.gpt_assistant_agent import GPTAssistantAgent
from nba_funcs import get_lineups
from db_tools import data_lookup


llm_config = {
    "timeout": 90,
    "config_list": CONFIG_LIST,
    "temperature": 0,
}


def get_agent(agent_call: str) -> dict:
    coll = DB['swarm_agents']
    agent_doc = coll.find_one({"call": agent_call, "org_name": "nba_autogen"})
    logging.info(f"Got agent - tools: {agent_doc['tools']} - instructions: {agent_doc['instructions']}")
    return agent_doc

# Create the agents


# NBA Analyst
# Grab the functions from the assistants.json file
nba_analyst_settings = get_agent('nba_analyst')
nba_analyst_config = llm_config.copy()
nba_analyst_config["tools"] = nba_analyst_settings['tools']
nba_analyst = GPTAssistantAgent(
    name="NBA_Analyst",
    instructions=nba_analyst_settings['instructions'],
    llm_config=nba_analyst_config
)

# NBA Data Guy
# Grab the functions from the assistants.json file
nba_data_guy_settings = get_agent('nba_data_guy')
nba_data_guy_config = llm_config.copy()
nba_data_guy_config["tools"] = nba_data_guy_settings['tools']
nba_data_guy = GPTAssistantAgent(
    name="NBA_Data_Guy",
    instructions=nba_data_guy_settings['instructions'],
    llm_config=nba_data_guy_config,
    function_map={
        "get_lineups": get_lineups,
    }
)

# Document Retriever
# Grab the functions from the assistants.json file
doc_retriever_settings = get_agent('doc_retriever')
doc_retriever_config = llm_config.copy()
doc_retriever_config["tools"] = doc_retriever_settings['tools']
doc_retriever = GPTAssistantAgent(
    name="Document_Retriever",
    instructions=doc_retriever_settings['instructions'],
    llm_config=doc_retriever_config,
    function_map={
        "data_lookup": data_lookup,
    }
)


# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    system_message="A human admin. Execute suggested function calls.",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="ALWAYS",
    max_consecutive_auto_reply=10,
    code_execution_config={
        "work_dir": "coding",
        "use_docker": True,
    }
)

agents = [user_proxy, nba_analyst, nba_data_guy, doc_retriever]
logging.info(f"Agents: {agents}")

# Create Group Chat
groupchat = autogen.GroupChat(
    agents=agents,
    messages=[],
    max_round=12
)

# Create Group Chat Manager
manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config=llm_config
)

user_proxy.initiate_chat(
    manager, message="What's the best GSW lineup that includes Kuminga?"
)
