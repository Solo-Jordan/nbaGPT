from dns.e164 import query

from settings import logging
from db_tools import get_agent_from_db, get_nba_data_guys
from agents.agents import Agent
from agents.nba_data_guy import nba_data_guy

from langchain import hub


def extrapolate_query(agent: Agent, init_query: str, nba_data_guy_tools: list) -> str:
    """
    Extrapolate the query. This call is made to best reasoning AI to extrapolate the query.
    :param agent: The agent object.
    :param init_query: The query to extrapolate.
    :param nba_data_guy_tools: The tools available for the NBA Data Guy.
    :return: The query.
    """

    # Load the LangChain Hub prompt template
    prompt_template = hub.pull("extrapolate_query_template")

    # Format the prompt with the query and available tools
    prompt = prompt_template.format(query=init_query, tools=nba_data_guy_tools)

    # Use the AI to generate the extrapolated query
    extrapolated_query = agent.one_off_message(prompt)

    return extrapolated_query


def planning_step(agent: Agent) -> str:
    """
    Break down the tasks and determine the data points needed.
    :param agent: The agent object.
    :return: The request.
    """

    # Pull the prompt
    prompt_template = hub.pull("oai_nba_analyst_plan")
    prompt = prompt_template.format()

    # Add the prompt to the conversation
    agent.add_message(prompt)

    # Run the agent
    request = agent.do_run()

    return request


def get_data(main_thread_id: str, request: str, ndg_id: str, data_guy: Agent = None) -> tuple[Agent, str]:
    """
    Get the data from the NBA API.
    :param main_thread_id: The main thread ID.
    :param request: The request.
    :param ndg_id: The NBA Data Guy ID.
    :param data_guy: The agent object. This is passed back if follow up requests are needed.
    :return: The data.
    """

    # Call the NBA Data Guy
    data_guy, data = nba_data_guy(main_thread_id, request, ndg_id, data_guy)

    return data_guy, data


def analyze_data(agent: Agent, data_guy: Agent, data: str, data_guy_id: str, message: str) -> str:
    """
    Analyze the data.
    :param agent: The agent object.
    :param data_guy: The data guy agent object.
    :param data: The data.
    :param data_guy_id: The data guy ID.
    :param message: The initial message.
    :return: The analysis.
    """

    # Pull the prompt
    prompt_template = hub.pull("oai_nba_analyst_eval")
    prompt = prompt_template.format(data=data, query=message)

    # Add the prompt to the conversation
    agent.add_message(prompt)

    # Run the agent
    evaluation = agent.do_run()

    # If the evaluation is not "yes", then follow up with the research team until it is.
    while "yes" not in evaluation.lower():
        msg = "Please respond with a follow up request to the reseach team."
        agent.add_message(msg)

        # Run the agent
        follow_up = agent.do_run()

        # Call the NBA Data Guy
        follow_up_data = get_data(agent.main_thread_id, follow_up, data_guy_id, data_guy)

        prompt = prompt_template.format(data=follow_up_data, query=message)
        agent.add_message(prompt)
        evaluation = agent.do_run()

    # Analyze the data
    analysis_prompt_template = hub.pull("oai_nba_analyst_analysis")
    analysis_prompt = analysis_prompt_template.format()
    agent.add_message(analysis_prompt)

    # Run the agent
    analysis = agent.do_run()

    return analysis


def nba_analyst(main_thread_id: str, message: str) -> str:

    # Get the agent from the database
    db_agent = get_agent_from_db("nba_analyst", "nba")

    # Initialize the agent
    logging.info("Initializing NBA Analyst.")
    analyst = Agent(
        name="nba_analyst",
        instructions=db_agent["instructions"],
        model=db_agent["model"],
        tools=db_agent["tools"],
        main_thread_id=main_thread_id
    )

    # Add the message to the conversation
    analyst.add_message(message)

    # Get list of nba_data_guy instances
    nba_data_guys = get_nba_data_guys()

    # Get the extrapolated query for each nba_data_guy
    all_data_requests = {}
    for data_guy in nba_data_guys:
        # Remove the data_lookup tool from the list of tools since we don't need the analyst to ask for that
        no_data_lookup_tools = [tool for tool in data_guy["tools"] if tool['function']['name'] != 'data_lookup']
        data_requests = extrapolate_query(analyst, message, no_data_lookup_tools)
        all_data_requests[f'nba_data_guy_{data_guy["id"]}'] = data_requests

    # Format string for each nba_data_guy
    requests_str = ""
    for data_guy_id, requests in all_data_requests.items():
        requests_str += f"{data_guy_id}: {requests}\n"

    # Add the requests to the conversation as the agent
    analyst.add_message(requests_str, as_agent=True)

    # Fetch data from each nba_data_guy
    all_data = {}
    for data_guy_id, requests in all_data_requests.items():
        # Get the data
        data_guy, data = get_data(main_thread_id, requests, data_guy_id.split("_")[-1])
        all_data[data_guy_id] = {"data": data, "agent": data_guy}

    # Analyze the data
    analysis = ""
    # For each data guy, analyze the data
    for data_guy_id, data_agent in all_data.items():
        data_guy = data_agent["agent"]
        data = data_agent["data"]
        # Since this is being done in a thread the last `analysis` will be the culmination of all the analysis
        analysis = analyze_data(analyst, data_guy, data, data_guy_id, message)

    return analysis
