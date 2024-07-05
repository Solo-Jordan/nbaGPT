from settings import logging
from db_tools import get_agent_from_db
from agents import Agent
from nba_data_guy import nba_data_guy

from langchain import hub


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


def get_data(main_thread_id: str, request: str, data_guy: Agent = None) -> tuple[Agent, str]:
    """
    Get the data from the NBA API.
    :param main_thread_id: The main thread ID.
    :param request: The request.
    :param data_guy: The agent object. This is passed back if follow up requests are needed.
    :return: The data.
    """

    # Call the NBA Data Guy
    data_guy, data = nba_data_guy(main_thread_id, request, data_guy)

    return data_guy, data


def analyze_data(agent: Agent, data_guy: Agent, data: str) -> str:
    """
    Analyze the data.
    :param agent: The agent object.
    :param data_guy: The data guy agent object.
    :param data: The data.
    :return: The analysis.
    """

    # Pull the prompt
    prompt_template = hub.pull("oai_nba_analyst_eval")
    prompt = prompt_template.format(data=data)

    # Add the prompt to the conversation
    agent.add_message(prompt)

    # Run the agent
    evaluation = agent.do_run()

    # If the evaluation is not "yes", then follow up with the research team until it is.
    while evaluation.lower() != "yes":
        msg = "Please respond with a follow up request to the reseach team."
        agent.add_message(msg)

        # Run the agent
        follow_up = agent.do_run()

        # Call the NBA Data Guy
        follow_up_data = get_data(agent.main_thread_id, follow_up, data_guy)

        prompt = prompt_template.format(data=follow_up_data)
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

    # Break down tasks and determine the data points needed
    request = planning_step(analyst)

    # Get the data
    data_guy, data = get_data(main_thread_id, request)

    # Analyze the data
    analysis = analyze_data(analyst, data_guy, data)

    return analysis
