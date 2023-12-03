import os
import logging.config
import yaml
import json
import datetime
import requests
import connexion

from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from flask import jsonify
from connexion import NoContent


if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    APP_CONF_FILE = "/config/app_conf.yml"
    LOG_CONF_FILE = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    APP_CONF_FILE = "app_conf.yml"
    LOG_CONF_FILE = "log_conf.yml"

with open(APP_CONF_FILE, 'r', encoding='utf-8') as f:
    app_config = yaml.safe_load(f.read())

with open(LOG_CONF_FILE, 'r', encoding='utf-8') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')
logger.info(f"App Conf File: {APP_CONF_FILE}")
logger.info(f"Log Conf File: {LOG_CONF_FILE}")

def getHealthStats():
    """ Periodically checks the health of services and updates their status """
    logger.info("Starting Health Check")

    if os.path.isfile(app_config["health_datastore"]["filename"]):
        with open(app_config["health_datastore"]["filename"], 'r') as fh:
            health_stats = json.load(fh)

        stats = {}
        if "audit_log" in health_stats:
            stats["audit_log"] = health_stats["audit_log"]
        if "processing" in health_stats:
            stats["processing"] = health_stats["processing"]
        if "storage" in health_stats:
            stats["storage"] = health_stats["storage"]
        if "receiver" in health_stats:
            stats["receiver"] = health_stats["receiver"]
        if "last_updated" in health_stats:
            stats["last_updated"] = health_stats["last_updated"]

        logger.info("Completed Health Check")
        logger.debug(health_stats)

        return health_stats, 200

    return NoContent, 404


def populate_stats():
    """ Gets the latest health stats object, or initializes it if not present """
    logger.info("Start Periodic Processing")

    stats = get_latest_health_stats()

    last_updated = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    current_timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    if "last_updated" in stats:
        last_updated = stats["last_updated"]
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Get new events using the last updated time and the current time
    for service_name, base_url in app_config["health_check"]["services"].items():
        # Construct the full URL for each service
        full_url = f"http://{base_url}?timestamp={last_updated}&end_timestamp={current_timestamp}"
        try:
            response = requests.get(full_url, timeout=5)
            # Process the response as needed
            logger.info(f"Response from {service_name} service: {response.status_code}")

            if response.status_code == 200:
                stats[service_name] = "Running"

        except requests.exceptions.RequestException as e:
            logger.error(f"Request to {service_name} failed: {e}")

    stats["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    write_health_stats(stats)

    logger.info("Done Periodic Processing")

def get_latest_health_stats():
    """ Health endpoint reading from the JSON file """
    if os.path.isfile(app_config["health_datastore"]["filename"]):
        with open(app_config["health_datastore"]["filename"], 'r') as f:
            health_stats = json.load(f)
            return jsonify(health_stats), 200

    return {"audit_log": "Down",
            "processing": "Down",
            "receiver": "Down",
            "storage": "Down",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}

def write_health_stats(stats):
    """ Writes health stats to a JSON file """
    fh = open(app_config["health_datastore"]["filename"], "w")
    fh.write(json.dumps(stats))
    fh.close()

def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=app_config['health_check']['interval'])
    sched.start()

app = connexion.FlaskApp(__name__, specification_dir='')

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("SoccerStats.yaml",
            strict_validation=True,
            validate_responses=True)

if __name__ == '__main__':
    init_scheduler()
    app.run(port=8120)
