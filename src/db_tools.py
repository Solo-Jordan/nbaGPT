from settings import logging, DB
from bson.objectid import ObjectId
import json


def doc_lookup(oid: str, query: dict) -> list | None:
    """
    Look up info in a doc. When info is sourced via api the agent will insert it into swarm_facts collection in one
    document. The data will be stored in an array of objects. Each object will have a key called "data" and the value
    will be the data. Ex doc:
    {
        "_id": ObjectId("65a32d4a80dc2240bf9d8cbc"),
        "data": [
            {
                "MIN": 100,
                "MAX": 1000
            },
            {
                "MIN": 1001,
                "MAX": 10000
            }
        ]
    }

    So this function will do queries on the data array and return the data that matches the query.
    :param oid: The id of the document.
    :param query: The query to find the info in the doc.
    :return: The document.
    """
    logging.info(f"Looking up info in doc: {oid}.")
    coll = DB['swarm_facts']

    # Aggregation pipeline
    pipeline = [
        {
            "$match": {
                "_id": ObjectId(oid)
            }
        },
        {
            "$project": {
                "data": {
                    "$filter": {
                        "input": "$data",
                        "as": "item",
                        "cond": query
                    }
                }
            }
        }
    ]

    # Executing the aggregation query
    result = coll.aggregate(pipeline)
    res_list = [res for res in result]

    return res_list


def data_lookup(doc_id: str, query: str) -> str:
    """
    Look up data in a doc.
    :param doc_id: The id of the document that you want to look up data in.
    :param query: The query to find the info in the doc.
    :return:
    """

    # Catch the error and send it to the assistant so they can correct how they use it.
    try:
        query_dict = json.loads(query)
        results = doc_lookup(doc_id, query_dict)
    except Exception as e:
        results = str(e)

    if not results:
        results = "This query returned no results. Please double check that you're query is setup correctly."
    else:
        results = str(results)

    return json.dumps({"query": query, "results": results})
