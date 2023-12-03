"""
This module integrates various components to set up and run a Flask application
with Kafka integration for processing and retrieving sports statistics. It includes
configuration loading, Kafka client setup, API initialization with Connexion, and
Flask CORS settings for cross-origin resource sharing. The module also contains
specific functions to interact with Kafka for fetching team and player statistics.
"""
import os
import json
import logging.config
import yaml
from pykafka import KafkaClient
from flask_cors import CORS
import connexion
from flask import jsonify

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


def getTeamStatistics(index):

    kafka_client = KafkaClient(
        hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    )
    kafka_topic = kafka_client.topics[str.encode(app_config["events"]["topic"])]

    consumer = kafka_topic.get_simple_consumer(reset_offset_on_start=True,
                                               consumer_timeout_ms=1000)

    logger.info(f"Retrieving Team Statistic at index {index}")

    event_messages = []

    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)


            if msg.get('type') == 'Team':
                event_messages.append(msg)

            if len(event_messages) > index:
                return event_messages[index], 200
    except:
        logger.error("No more messages found")

    logger.error(f"Could not find Team statistic at index {index}")
    return { "message": "Not Found" }, 404


def getPlayerStatistics(index):

    kafka_client = KafkaClient(
        hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    )
    kafka_topic = kafka_client.topics[str.encode(app_config["events"]["topic"])]

    consumer = kafka_topic.get_simple_consumer(reset_offset_on_start=True,
                                               consumer_timeout_ms=1000)

    logger.info(f"Retrieving Player Statistic at index {index}")

    event_messages = []

    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)


            if msg.get('type') == 'Player':
                event_messages.append(msg)

            if len(event_messages) > index:
                return event_messages[index], 200
    except:
        logger.error("Nore more messages found")

    logger.error(f"Could not find Player statistic at index {index}")
    return { "message": "Not Found"}, 404

def health():
    return jsonify({"status": "healthy"}), 200

app = connexion.FlaskApp(__name__, specification_dir='')

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("SoccerStats.yaml",
            strict_validation=True,
            validate_responses=True,
            base_path="/audit_log")

if __name__ == '__main__':
    app.run(port=8110)
