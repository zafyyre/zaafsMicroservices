import connexion
import yaml
import logging, logging.config
import datetime
import os
import json
import requests

from apscheduler.schedulers.background import BackgroundScheduler
from connexion import NoContent
from flask_cors import CORS


if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"
with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())
# External Logging Configuration
with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)


def getStats():
    """ Gets processing stats """

    if os.path.isfile(app_config["datastore"]["filename"]):
        fh = open(app_config["datastore"]["filename"])
        all_stats = json.load(fh)
        fh.close()

        stats = {}
        if "num_of_teams" in all_stats:
            stats["num_of_teams"] = all_stats["num_of_teams"]
        if "max_team_goals" in all_stats:
            stats["max_team_goals"] = all_stats["max_team_goals"]
        if "max_player_age" in all_stats:
            stats["max_player_age"] = all_stats["max_player_age"]
        if "max_player_goals" in all_stats:
            stats["max_player_goals"] = all_stats["max_player_goals"]
        if "last_updated" in all_stats:
            stats["last_updated"] = all_stats["last_updated"]

        logger.info("Found valid stats")
        logger.debug(stats)

        return stats, 200

    return NoContent, 404

def populate_stats():
    """ Periodically update stats """
    logger.info("Start Periodic Processing")
    logger.info("Zaaf Test")

    stats = get_latest_processing_stats()

    last_updated = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    current_timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    if "last_updated" in stats:
        last_updated = stats["last_updated"]
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Get new events using the last updated time and the current time
    response = requests.get(app_config["eventstore"]["url"] + "/teams?timestamp=" + last_updated + "&end_timestamp=" + current_timestamp)

    if response.status_code == 200:
        if "num_of_teams" in stats.keys():
            stats["num_of_teams"] += len(response.json())
        else:
            stats["num_of_teams"] = len(response.json())

        for event in response.json():
            if "max_team_goals" in stats.keys() and \
                    event["goals"] > stats["max_team_goals"]:
                stats["max_team_goals"] = event["goals"]
            elif "max_team_goals" not in stats.keys():
                stats["max_team_goals"] = event["goals"]
            
            logger.debug("Processed Team event with id of %s" % event["trace_id"])

        logger.info("Processed %d Team statistics" % len(response.json()))

    # Get new events using the last updated time and the current time
    response = requests.get(app_config["eventstore"]["url"] + "/players?timestamp=" + last_updated + "&end_timestamp=" + current_timestamp)

    if response.status_code == 200:
        for event in response.json():
            if "max_player_age" in stats.keys() and \
                    event["age"] > stats["max_player_age"]:
                stats["max_player_age"] = event["age"]
            elif "max_player_age" not in stats.keys():
                stats["max_player_age"] = event["age"]

        for event in response.json():
            if "max_player_goals" in stats.keys() and \
                    event["goals"] > stats["max_player_goals"]:
                stats["max_player_goals"] = event["goals"]
            elif "max_player_goals" not in stats.keys():
                stats["max_player_goals"] = event["goals"]
            
            logger.debug("Processed Player event with id of %s" % event["trace_id"])

        logger.info("Processed %d Player statistics" % len(response.json()))

    stats["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    write_processing_stats(stats)

    logger.info("Done Periodic Processing")


def get_latest_processing_stats():
    """ Gets the latest stats object, or None if there isn't one """
    if os.path.isfile(app_config["datastore"]["filename"]):
        fh = open(app_config["datastore"]["filename"])
        full_stats = json.load(fh)
        fh.close()
        return full_stats

    return {"num_of_teams": 0,
            "max_team_goals": 0,
            "max_player_age": 0,
            "max_player_goals": 0,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}


def write_processing_stats(stats):
    """ Writes a new stats object """
    fh = open(app_config["datastore"]["filename"], "w")
    fh.write(json.dumps(stats))
    fh.close()


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,'interval',seconds=app_config['scheduler']['period_sec'])
    sched.start()

def health():
    return "OK", 200

app = connexion.FlaskApp(__name__, specification_dir='')

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("SoccerStats.yaml", strict_validation=True, validate_responses=True, base_path="/processing")


if __name__ == '__main__':
    init_scheduler()
    app.run(port=8100, use_reloader=False)