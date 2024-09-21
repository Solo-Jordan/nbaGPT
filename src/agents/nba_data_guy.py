from settings import logging
from db_tools import get_agent_from_db
from agents.agents import Agent
from agent_tools.nba_api_tools import function_map as nba_api_tools_function_map

function_map = {
    "1": nba_api_tools_function_map
}


def nba_data_guy(main_thread_id: str, request: str, ndg_id: str, data_guy: Agent) -> tuple[Agent, str]:
    """
    Get the data from the NBA API.
    :param main_thread_id: The main thread ID.
    :param request: The request.
    :param ndg_id: The NBA Data Guy ID.
    :param data_guy: The agent object. This is passed back if follow up requests are needed.
    :return: The data.
    """

    if not data_guy:
        logging.info(f"Initializing NBA Data Guy. ID: {ndg_id}")

        # Get the agent from the database
        db_agent = get_agent_from_db("nba_data_guy", "nba", ndg_id)

        # Initialize the agent
        data_guy = Agent(
            name="nba_data_guy",
            instructions=db_agent["instructions"],
            model=db_agent["model"],
            tools=db_agent["tools"],
            main_thread_id=main_thread_id,
            function_map=function_map[ndg_id]
        )

    # Add the request to the conversation
    data_guy.add_message(request)

    # Run the agent
    data = data_guy.do_run()

    return data_guy, data
