from settings import logging, DB
from nba_api.stats import endpoints
import json


TEAM_REF = {
    '1610612739': 'Cleveland Cavaliers',
    '1610612740': 'New Orleans Pelicans',
    '1610612741': 'Chicago Bulls',
    '1610612742': 'Dallas Mavericks',
    '1610612743': 'Denver Nuggets',
    '1610612744': 'Golden State Warriors',
    '1610612745': 'Houston Rockets',
    '1610612746': 'Los Angeles Clippers',
    '1610612747': 'Los Angeles Lakers',
    '1610612748': 'Miami Heat',
    '1610612749': 'Milwaukee Bucks',
    '1610612750': 'Minnesota Timberwolves',
    '1610612751': 'Brooklyn Nets',
    '1610612752': 'New York Knicks',
    '1610612753': 'Orlando Magic',
    '1610612754': 'Indiana Pacers',
    '1610612755': 'Philadelphia 76ers',
    '1610612756': 'Phoenix Suns',
    '1610612757': 'Portland Trail Blazers',
    '1610612758': 'Sacramento Kings',
    '1610612759': 'San Antonio Spurs',
    '1610612760': 'Oklahoma City Thunder',
    '1610612761': 'Toronto Raptors',
    '1610612762': 'Utah Jazz',
    '1610612763': 'Memphis Grizzlies',
    '1610612764': 'Washington Wizards',
    '1610612765': 'Detroit Pistons',
    '1610612766': 'Charlotte Hornets',
    '1610612737': 'Atlanta Hawks',
    '1610612738': 'Boston Celtics'
}


def generic_create(collection: str, content: dict | list) -> str | bool:
    """
    Create a document in the database.
    :param collection: The collection name to create the document in.
    :param content: The content of the document.
    :return: The ID of the document.
    """
    logging.info(f"Creating document in {collection}.")
    coll = DB[collection]
    try:
        doc_id = coll.insert_one(content).inserted_id
        logging.info(f"Created document in {collection}.")
        return doc_id
    except Exception as e:
        logging.error(f"Failed to create document in {collection}. Error: {e}")
        return False


def get_lineups(**kwargs):
    """
    Get lineups for a team.
    :param team_id_nullable: The ID of the team you want lineups for.
    :param last_n_games: The number of games to look back. If not provided, will look at all games.
    :param opponent_team_id: The ID of the opponent team. If not provided, will look at all opponents.
    :param period: The period to look at. If not provided, will look at all periods.
    :param location_nullable: The location to look at ('Home', 'Away'). If not provided, will look at all locations.
    :param outcome_nullable: The outcome to look at ('W', 'L'). If not provided, will look at all outcomes.
    :return: The lineups.
    """

    season = '2023-24'
    measure_type_detailed_defense = 'Advanced'

    kwargs['season'] = '2023-24'
    kwargs['measure_type_detailed_defense'] = 'Advanced'

    # Get the lineups
    try:
        logging.info(f"Fetching lineup for team_id: {TEAM_REF[kwargs['team_id_nullable']]}")
        data = endpoints.leaguedashlineups.LeagueDashLineups(**kwargs).get_data_frames()[0]
        logging.debug('Data fetched successfully')
    except Exception as e:
        logging.error(f'Failed to fetch lineup for team_id: {TEAM_REF[kwargs["team_id_nullable"]]}. Error: {e}')
        return json.dumps(
            {
                "status": "error",
                "msg": f'Failed to fetch lineup for team_id: {TEAM_REF[kwargs["team_id_nullable"]]}. Error: {e}'
            }
        )

    lineups = {"data": data.to_dict('records')}

    schema_example = lineups['data'][0]
    logging.info(f"Schema example: {schema_example}")

    # Add the lineups to the database
    create_result = generic_create(
        collection='swarm_facts',
        content=lineups
    )

    # generic_create returns False if the insert fails and the ID of the insert if it succeeds.
    if create_result:
        logging.info(f"Added lineups to DB.")

        return json.dumps(
            {
                "args": kwargs,
                "msg": f"Lineups added to DB with ID: {create_result}\n\nExample entry:\n{schema_example}"
            }
        )
    else:
        logging.error(f"Failed to add lineups to DB.")
        return json.dumps({"args": kwargs, "msg": "Failed to add lineups to DB."})


# I'll use this later when I add more funcitons
func_map = {
    'get_lineups': get_lineups
}
