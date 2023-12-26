from settings import logging
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


def get_lineups(**kwargs):
    """
    Get the lineups for a given team.
    :return: The lineups.
    """

    kwargs['season'] = '2023-24'

    # Get the lineups
    try:
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

    # Filter out lineups with less than 10 minutes played so we don't go over token limit on the response to assistant.
    ten_plus_min_lineups = [lineup for lineup in data.to_dict('records') if lineup['MIN'] >= 10.0]

    return json.dumps({"status": "success", "msg": ten_plus_min_lineups})


funcs = {
    'get_lineups': get_lineups
}
