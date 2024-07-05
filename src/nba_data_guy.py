from settings import logging
from db_tools import get_agent_from_db
from agents import Agent
from agent_tools.nba_data_guy import function_map


def nba_data_guy(main_thread_id: str, request: str, data_guy: Agent) -> tuple[Agent, str]:
    """
    Get the data from the NBA API.
    :param main_thread_id: The main thread ID.
    :param request: The request.
    :param data_guy: The agent object. This is passed back if follow up requests are needed.
    :return: The data.
    """

    if not data_guy:
        # Get the agent from the database
        db_agent = get_agent_from_db("nba_data_guy", "nba")

        # Initialize the agent
        logging.info("Initializing NBA Data Guy.")
        data_guy = Agent(
            name="nba_data_guy",
            instructions=db_agent["instructions"],
            model=db_agent["model"],
            tools=db_agent["tools"],
            main_thread_id=main_thread_id,
            function_map=function_map
        )

    # Add the request to the conversation
    data_guy.add_message(request)

    # Run the agent
    data = data_guy.do_run()

    return data_guy, data
