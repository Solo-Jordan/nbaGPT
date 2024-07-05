from settings import logging
from db_tools import get_agent_from_db
from agents import Agent
from agent_tools.nba_analyst import function_map


def nba_analyst(main_thread_id: str, message: str):

    # Get the agent from the database
    db_agent = get_agent_from_db("nba_analyst", "nba")

    # Initialize the agent
    logging.info("Initializing NBA Analyst.")
    analyst = Agent(
        name="nba_analyst",
        instructions=db_agent["instructions"],
        model=db_agent["model"],
        tools=db_agent["tools"],
        main_thread_id=main_thread_id,
        function_map=function_map
    )

    # Add the message to the conversation
    analyst.add_message(message)



