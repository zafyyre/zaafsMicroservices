import connexion
import json
import yaml
import logging, logging.config
import os

from pykafka import KafkaClient
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

# kafka_client = KafkaClient(hosts='%s:%d' % (app_config["events"]["hostname"], app_config["events"]["port"]))
# kafka_topic = kafka_client.topics[str.encode(app_config["events"]["topic"])]
# kafka_producer = kafka_topic.get_sync_producer()


def getTeamStatistics(index):

    kafka_client = KafkaClient(hosts='%s:%d' % (app_config["events"]["hostname"], app_config["events"]["port"]))
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

    kafka_client = KafkaClient(hosts='%s:%d' % (app_config["events"]["hostname"], app_config["events"]["port"]))
    kafka_topic = kafka_client.topics[str.encode(app_config["events"]["topic"])]

    consumer = kafka_topic.get_simple_consumer(reset_offset_on_start=True,
                                               consumer_timeout_ms=1000)

    logger.info("Retrieving Player Statistic at index {}".format(index))

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

    logger.error("Could not find Player statistic at index {}".format(index))
    return { "message": "Not Found"}, 404

app = connexion.FlaskApp(__name__, specification_dir='')

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("SoccerStats.yaml", strict_validation=True, validate_responses=True, base_path="/audit_log")

if __name__ == '__main__':
    app.run(port=8110)