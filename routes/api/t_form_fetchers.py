from flask import jsonify

from helpers.data_fetcher import get_levels, get_stat_groups, get_teams

from routes.api import api_bp


# Route to fetch levels for a given season.
@api_bp.route('/gamefetcher/get_levels/<season>')
def get_levels_endpoint(season):
    levels = get_levels(season)
    return jsonify(levels)

# Route to fetch statistic groups for a given level.
@api_bp.route('/gamefetcher/get_statgroups/<season>/<level_id>/<district_id>')
def get_statgroups(season, level_id, district_id=0):
    stat_groups = get_stat_groups(season, level_id, district_id)
    return jsonify(stat_groups)

# Route to fetch teams for a given statistic group.
@api_bp.route('/gamefetcher/get_teams/<season>/<stat_group_id>')
def get_teams_endpoint(season, stat_group_id):
    teams = get_teams(season, stat_group_id)
    return jsonify(teams)