from settings import logging, DB, SYS_MODE
from pymongo import ASCENDING, DESCENDING
from bson.json_util import dumps


def create_convo_doc(main_thread_id: str) -> None:
    """
    Create a convo document in the DB.
    :param main_thread_id: This is the ID of the main thread. This is a constant in the system.
    :return:
    """

    _coll = DB.get_collection("swarm_convos")
    _coll.insert_one(
        {
            "id": main_thread_id,
            "org_name": "nba",
            "convo": []
        }
    )
    logging.info("Created convo in DB.")
    return


def add_to_convo(main_thread_id: str, msg_dict: dict) -> bool:
    """
    Add a message to the conversation in the database.
    :param main_thread_id: The main thread ID.
    :param msg_dict: The message to add.
    :return:
    """

    convos = DB['swarm_convos']

    logging.info("Adding to convo in DB.")

    # If the system is in testing mode, then don't add to the DB.
    if SYS_MODE == "testing":
        logging.info("Mode is testing. Not adding to convo.")
        return True

    try:
        convos.update_one(
            {"id": main_thread_id},
            {
                "$push": {
                    "convo": msg_dict
                }
            }
        )
    except Exception as e:
        logging.error(f"Failed to add to convo. Error: {e}")
        return False

    return True


def get_agent_from_db(agent_call: str, org_name: str, agent_id: str = None) -> dict:
    """
    Get an agent from the database.
    :param agent_call: The agent call.
    :param org_name: The org name.
    :param agent_id: The agent ID. Used for NBA Data Guys.
    :return: The agent.
    """

    agents = DB['swarm_agents']

    logging.info(f"Getting {agent_call} from DB.")

    if agent_id:
        try:
            agent = agents.find_one(
                {
                    "call": agent_call,
                    "org_name": org_name,
                    "id": agent_id
                }
            )
        except Exception as e:
            logging.error(f"Failed to get agent from DB. Error: {e}")
            return {}
    else:
        try:
            agent = agents.find_one(
                {
                    "call": agent_call,
                    "org_name": org_name
                }
            )
        except Exception as e:
            logging.error(f"Failed to get agent from DB. Error: {e}")
            return {}

    logging.info(f"Got {agent['call']} from DB.")
    return agent


def doc_lookup(query: dict, sort: str | None, limit: int | None) -> str:
    """
    Look up info in a collection. When info is sourced via api the agent will insert it into swarm_facts collection.
    If the data is a list of dictionaries then they will be inserted as separate documents with a shared ID.
    This id is used to look up the data in the collection. If the data is a single dictionary then it will be inserted
    as a single document with the id of the document being the doc_id.
    :param query: The query to find the info in the doc this will include the ID.
    :param sort: The sort order.
    :param limit: The number of documents to return.
    :return: The document.
    """

    # Parse the sort
    sort_map = {
        "ASCENDING": ASCENDING,
        "DESCENDING": DESCENDING
    }

    sort_list = []
    if sort:
        sort_options = sort.split(",")
        # I could do list comprehension here but I want to keep it readable.
        for sort_option in sort_options:
            sort_tuple = tuple(sort_option.split(":"))
            sort_list.append((sort_tuple[0], sort_map[sort_tuple[1]]))

    coll = DB['swarm_facts']

    try:
        if sort_list and limit:
            data = coll.find(query).sort(sort_list).limit(limit)
        elif sort_list:
            data = coll.find(query).sort(sort_list)
        elif limit:
            data = coll.find(query).limit(limit)
        else:
            data = coll.find(query)
        logging.info("Found info in doc/s.")
    except Exception as e:
        logging.error(f"Failed to find info in doc/s. Error: {e}")
        return f"Failed to find info in doc/s. Error: {e}"

    # Convert to list of dictionaries
    data_list = []
    for doc in data:
        # Remove the ID field from the document so it doesn't confuse the agent
        del doc["_id"]
        data_list.append(dumps(doc))
    return str(data_list)


def generic_create(collection: str, content: dict | list) -> bool:
    """
    Create a document in the database.
    :param collection: The collection name to create the document in.
    :param content: The content of the document.
    :return: The ID of the document.
    """
    logging.info(f"Creating document in {collection}.")
    coll = DB[collection]

    # If content is a dictionary then insert one document. If it is a list then insert many documents.
    if isinstance(content, dict):
        try:
            coll.insert_one(content)
            logging.info(f"Created document in {collection}.")
            return True
        except Exception as e:
            logging.error(f"Failed to create document in {collection}. Error: {e}")
            return False
    elif isinstance(content, list):
        try:
            coll.insert_many(content)
            logging.info(f"Created documents in {collection}.")
            return True
        except Exception as e:
            logging.error(f"Failed to create documents in {collection}. Error: {e}")
            return False


def generic_update(collection: str, query: dict, content: dict | list) -> bool:
    """
    Update a document in the database.
    :param collection: The collection name to update the document in.
    :param query: The query to find the document to update.
    :param content: The content of the document.
    :return: The ID of the document.
    """
    logging.info(f"Updating document in {collection}.")
    coll = DB[collection]
    try:
        coll.update_one(query, content)
        logging.info(f"Updated document in {collection}.")
        return True
    except Exception as e:
        logging.error(f"Failed to update document in {collection}. Error: {e}")
        return False


def get_nba_data_guys() -> list:
    """
    Get the tools for the NBA Data Guy.
    :return: All of the NBA Data Guys
    """
    swarm_agents = DB['swarm_agents']

    logging.info(f"Getting tools for NBA Data Guy.")

    try:
        agents = swarm_agents.find(
            {
                "call": "nba_data_guy"
            }
        )
    except Exception as e:
        logging.error(f"Failed to get tools for NBA Data Guy. Error: {e}")
        return []

    return agents
