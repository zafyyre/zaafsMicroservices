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

def getHealth():
    """ Periodically checks the health of services and updates their status """
    logger.info("Starting Health Check")

    if os.path.isfile(app_config["health_datastore"]["filename"]):
        with open(app_config["health_datastore"]["filename"], 'r') as fh:
            health_stats = json.load(fh)
    else:
        # Initialize health_stats if the file does not exist
        health_stats = {service: {"status": "unknown", "last_checked": None}
                        for service in app_config['health_check']['services'].keys()}

    for service_name, url in app_config['health_check']['services'].items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                status = "running"
            else:
                status = "down"
        except requests.exceptions.RequestException:
            status = "down"

        health_stats[service_name] = {
            "status": status,
            "last_checked": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        }

    write_health_stats(health_stats)
    logger.info("Completed Health Check")


def get_latest_health_stats():
    """ Gets the latest health stats object, or initializes it if not present """
    if os.path.isfile(app_config["health_datastore"]["filename"]):
        with open(app_config["health_datastore"]["filename"], 'r') as f:
            return json.load(f)

    return {service: {"status": "unknown", "last_checked": None} for service in app_config['health_check']['services']}

def write_health_stats(stats):
    """ Writes health stats to a JSON file """
    with open(app_config["health_datastore"]["filename"], 'w') as fh:
        json.dump(stats, fh)

def health():
    """ Health endpoint reading from the JSON file """
    if os.path.isfile(app_config["health_datastore"]["filename"]):
        with open(app_config["health_datastore"]["filename"], 'r') as f:
            health_stats = json.load(f)
            return jsonify(health_stats), 200

    return {"audit_log": "down",
            "processing": "down",
            "receiver": "down",
            "storage": "down",
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")}

def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(getHealth, 'interval', seconds=app_config['health_check']['interval'])
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
