from settings import logging
from nba_api.stats import endpoints
from db_tools import generic_create, doc_lookup
import uuid
from datetime import datetime
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

SEASON = '2023-24'


def get_info(endpoint, endpoint_name, **kwargs) -> tuple[dict, str | None]:
    # Set the shared ID that will be used to identify the data in the DB
    doc_id = str(uuid.uuid4())

    # Get the lineups
    try:
        data = endpoint(**kwargs).get_data_frames()[0]
        logging.debug('Data fetched successfully')
    except Exception as e:
        logging.error(f'Failed to fetch {endpoint_name}. Error: {e}')
        return {}, None

    # Convert the data to a list of dictionaries
    data_list = data.to_dict('records')

    return data_list, doc_id


def add_info_to_db(data_list, doc_id, endpoint_name, hint) -> str:
    # Add the ID and the current time to the data
    current_time = datetime.utcnow()
    for item in data_list:
        item['createdAt'] = current_time
        item['doc_id'] = doc_id

    schema_example = data_list[0]
    logging.info(f"Schema example: {schema_example}")

    # Add the info to the database
    create_result = generic_create(collection='swarm_facts', content=data_list)

    # generic_create returns False if the insert fails and the ID of the insert if it succeeds.
    if create_result:
        logging.info(f"Added lineups to DB.")

        dba_msg = (f"\n\nNEXT STEP: You have successfully added the {endpoint_name} info to the database. Using the "
                   "info above you can now use the data_lookup function to query the data.\n\n")
        msg = (f"{endpoint_name} info added to DB with doc_id: "
               f"{doc_id}\n\nExample entry:\n{schema_example}{dba_msg}{hint}")
        return msg
    else:
        logging.error(f"Failed to add lineups to DB.")
        return f"Failed to add {endpoint_name} info to DB."


def get_lineups(**kwargs) -> str:
    """
    Get lineup stats. This function will source data relating to on court lineups for a team.
    Expected Data:
    - GROUP_SET
    - GROUP_ID
    - GROUP_NAME
    - TEAM_ID
    - TEAM_ABBREVIATION
    - GP
    - W
    - L
    - W_PCT
    - MIN
    - FGM
    - FGA
    - FG_PCT
    - FG3M
    - FG3A
    - FG3_PCT
    - FTM
    - FTA
    - FT_PCT
    - OREB
    - DREB
    - REB
    - AST
    - TOV
    - STL
    - BLK
    - BLKA
    - PF
    - PFD
    - PTS
    - PLUS_MINUS
    - GP_RANK
    - W_RANK
    - L_RANK
    - W_PCT_RANK
    - MIN_RANK
    - FGM_RANK
    - FGA_RANK
    - FG_PCT_RANK
    - FG3M_RANK
    - FG3A_RANK
    - FG3_PCT_RANK
    - FTM_RANK
    - FTA_RANK
    - FT_PCT_RANK
    - OREB_RANK
    - DREB_RANK
    - REB_RANK
    - AST_RANK
    - TOV_RANK
    - STL_RANK
    - BLK_RANK
    - BLKA_RANK
    - PF_RANK
    - PFD_RANK
    - PTS_RANK
    - PLUS_MINUS_RANK
    """
    kwargs['season'] = SEASON
    kwargs['measure_type_detailed_defense'] = 'Advanced'

    # Get the lineups
    data_list, doc_id = get_info(
        endpoint=endpoints.leaguedashlineups.LeagueDashLineups,
        endpoint_name='lineups',
        **kwargs
    )

    # Remove all lineups with less than 1 minute played
    data_list = [lineup for lineup in data_list if lineup['MIN'] >= 1]

    if not data_list:
        return "No lineups found."

    hint = ("Some things to consider when looking at lineup data:\n\n- You should consider sample size of lineups. "
            "Maybe include games played or minutes played in your query.\n- Net rating should generally be used as the "
            "overall metric for lineup performance.\n- If you are looking for specific lineup combinations, you should "
            "include the players' surname(s) in the query when doing a lookup.")
    # Add the lineups to the database
    msg = add_info_to_db(data_list, doc_id, 'lineups', hint)

    return msg


def get_hustle_stats_team(**kwargs) -> str:
    """
    Get team hustle stats. This function will source data relating to team hustle stats. Stats are per game.
    Expected Data:
    - TEAM_ID
    - TEAM_NAME
    - MIN
    - CONTESTED_SHOTS
    - CONTESTED_SHOTS_2PT
    - CONTESTED_SHOTS_3PT
    - DEFLECTIONS
    - CHARGES_DRAWN
    - SCREEN_ASSISTS
    - SCREEN_AST_PTS
    - OFF_LOOSE_BALLS_RECOVERED
    - DEF_LOOSE_BALLS_RECOVERED
    - LOOSE_BALLS_RECOVERED
    - PCT_LOOSE_BALLS_RECOVERED_OFF: Percentage of loose balls recovered by the team on offense
    - PCT_LOOSE_BALLS_RECOVERED_DEF: Percentage of loose balls recovered by the team on defense
    - OFF_BOXOUTS
    - DEF_BOXOUTS
    - BOX_OUTS
    - PCT_BOX_OUTS_OFF
    - PCT_BOX_OUTS_DEF
    """

    # Set defaults for required parameters
    kwargs['season'] = SEASON
    kwargs['per_mode_time'] = 'PerGame'

    # Get the hustle stats
    data_list, doc_id = get_info(
        endpoint=endpoints.leaguehustlestatsteam.LeagueHustleStatsTeam,
        endpoint_name='hustle_stats_team',
        **kwargs
    )

    if not data_list:
        return "No hustle stats found."

    hint = ("Some things to consider when looking at hustle stats:\n\n- Deflections are a good indicator of defensive "
            "activity.\n- Charges drawn are a good indicator of defensive positioning.\n- Screen assists are a good "
            "indicator of offensive activity.")

    # Add the hustle stats to the database
    msg = add_info_to_db(data_list, doc_id, 'hustle_stats_team', hint)

    return msg


def get_player_clutch_stats(**kwargs) -> str:
    """
    Get player clutch stats. This function will source data relating to clutch performance for players.
    Expected Data:
    - GROUP_SET
    - PLAYER_ID
    - PLAYER_NAME
    - TEAM_ID
    - TEAM_ABBREVIATION
    - AGE
    - GP
    - W
    - L
    - W_PCT
    - MIN
    - FGM
    - FGA
    - FG_PCT
    - FG3M
    - FG3A
    - FG3_PCT
    - FTM
    - FTA
    - FT_PCT
    - OREB
    - DREB
    - REB
    - AST
    - TOV
    - STL
    - BLK
    - BLKA
    - PF
    - PFD
    - PTS
    - PLUS_MINUS
    - NBA_FANTASY_PTS
    - DD2
    - TD3
    - GP_RANK
    - W_RANK
    - L_RANK
    - W_PCT_RANK
    - MIN_RANK
    - FGM_RANK
    - FGA_RANK
    - FG_PCT_RANK
    - FG3M_RANK
    - FG3A_RANK
    - FG3_PCT_RANK
    - FTM_RANK
    - FTA_RANK
    - FT_PCT_RANK
    - OREB_RANK
    - DREB_RANK
    - REB_RANK
    - AST_RANK
    - TOV_RANK
    - STL_RANK
    - BLK_RANK
    - BLKA_RANK
    - PF_RANK
    - PFD_RANK
    - PTS_RANK
    """
    kwargs['season'] = SEASON

    # Get the player clutch stats
    data_list, doc_id = get_info(
        endpoint=endpoints.leaguedashplayerclutch.LeagueDashPlayerClutch,
        endpoint_name='player_clutch_stats',
        **kwargs
    )

    if not data_list:
        return "No player clutch stats found."

    hint = ("Some things to consider when looking at player clutch stats:\n\n- Clutch stats are generally defined as "
            "stats in the last 5 minutes of a game within 5 points.\n- The RANK columns are useful for comparing "
            "players to the rest of the league.\n- You can lookup all players from a team by including the TEAM_ID "
            "in the query.")

    # Add the player clutch stats to the database
    msg = add_info_to_db(data_list, doc_id, 'player_clutch_stats', hint)

    return msg


def get_player_stats() -> str:
    """
    Get player stats. This function will source data relating to player performance stats for all players. This function
    can also be used to get a player's ID to use in other functions.
    Expected Data:
    - PLAYER_ID
    - PLAYER_NAME
    - TEAM_ID
    - AGE
    - GP
    - W
    - L
    - W_PCT
    - MIN
    - FGM
    - FGA
    - FG_PCT
    - FG3M
    - FG3A
    - FG3_PCT
    - FTM
    - FTA
    - FT_PCT
    - OREB
    - DREB
    - REB
    - AST
    - TOV
    - STL
    - BLK
    - BLKA
    - PF
    - PFD
    - PTS
    - PLUS_MINUS
    - DD2
    - TD3
    """
    kwargs = {
        'season': SEASON
    }

    # Get the player stats
    data_list, doc_id = get_info(
        endpoint=endpoints.leaguedashplayerstats.LeagueDashPlayerStats,
        endpoint_name='player_stats',
        **kwargs
    )

    if not data_list:
        return "Could not retrieve player stats."

    hint = ("Some things to consider when looking at player stats:\n\n- You can lookup all players from a team by "
            "including the TEAM_ID in the query.\n- PLUS_MINUS should be used as a general indicator of a player's "
            "performance.")

    # Add the player stats to the database
    msg = add_info_to_db(data_list, doc_id, 'player_stats', hint)

    return msg


def data_lookup(query: str, sort: str = None, limit: int = None) -> str:
    """
    Lookup data in the database. This function is used to retrieve specific document data based on a given document
    ID and query.  All queries should include the id as `doc_id`. Examples:

    For since doc lookup:
    ```
    {"doc_id": "0000-1111-2222-3333-4444"}
    ```

    For multiple doc lookup:
    ```
    {"doc_id": "0000-1111-2222-3333-4444", "name": "John"}
    ```
    """

    query_dict = json.loads(query)

    return doc_lookup(query=query_dict, sort=sort, limit=limit)


function_map = {
    "get_lineups": get_lineups,
    "get_hustle_stats_team": get_hustle_stats_team,
    "get_player_clutch_stats": get_player_clutch_stats,
    "get_player_stats": get_player_stats,
    "data_lookup": data_lookup
}
