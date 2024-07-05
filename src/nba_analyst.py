from settings import logging
from db_tools import get_agent_from_db, add_to_convo
from agents import Agent
from langchain import hub


def planning_step(agent: Agent) -> str:
    """
    Break down the tasks and determine the data points needed.
    :param agent: The agent object.
    :return: The request.
    """

    # Pull the prompt
    prompt = hub.pull("oai_nba_analyst_plan")

    # Add the prompt to the conversation
    agent.add_message(prompt)

    # Run the agent
    request = agent.do_run()

    return request


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
    request = planning_step(analyst, main_thread_id)

    # Get the data
    data = get_data(request)

    # Analyze the data
    analysis = analyze_data(analyst, data)

    # Generate a response
    response = generate_response(analyst, analysis)

    return response



