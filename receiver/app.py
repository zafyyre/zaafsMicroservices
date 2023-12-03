import datetime
import json
import logging
import logging.config
import os
import time
import uuid
import yaml

import connexion
from connexion import NoContent
from pykafka import KafkaClient
from pykafka.exceptions import KafkaException
from flask import jsonify

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    APP_CONF_FILE = "/config/app_conf.yml"
    LOG_CONF_FILE = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    APP_CONF_FILE = "app_conf.yml"
    LOG_CONF_FILE = "log_conf.yml"
with open(APP_CONF_FILE, 'r') as f:
    app_config = yaml.safe_load(f.read())
# External Logging Configuration
with open(LOG_CONF_FILE, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % APP_CONF_FILE)
logger.info("Log Conf File: %s" % LOG_CONF_FILE)

# Configure the hostname from the application configuration
hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
# Set the maximum number of retries for connecting to Kafka
max_retries = app_config["kafka"]["max_retries"]
# Set the wait time between retry attempts
retry_wait = app_config["kafka"]["retry_wait"]
# Initialize the attempt counter
attempt = 0

# Begin a loop that will try to connect to Kafka up to the max_retries limit
while attempt < max_retries:
    try:
        # Log the attempt number
        logger.info(f"Attempt {attempt+1} of {max_retries}: Connecting to Kafka at {hostname}")
        # Attempt to create a Kafka client
        client = KafkaClient(hosts=hostname)
        # Attempt to access the Kafka topic and producer
        topic = client.topics[str.encode(app_config["events"]["topic"])]
        # If successful, log the success and break out of the loop
        logger.info("Successfully connected to Kafka")
        break
    except KafkaException as e:
        # If a KafkaException occurs, log the failure
        logger.error(f"Failed to connect to Kafka: {e}")
        # Increment the attempt counter
        attempt += 1
        # If we have not reached the max_retries limit, wait for a bit and then continue the loop
        if attempt < max_retries:
            logger.info(f"Retrying in {retry_wait} seconds...")
            time.sleep(retry_wait)
        else:
            # If we've reached the max_retries limit, log an error and exit the function
            logger.error("Maximum retry attempts reached, could not connect to Kafka.")


def teamStatistics(body):
    trace_id = uuid.uuid4()
    body['trace_id'] = str(trace_id)

    logger.info("Received Event Team Request with Team ID: {} and Trace ID: {}".format(body["team_id"], body["trace_id"]))

    msg = {
        "type": "Team",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body
    }
    msg_str = json.dumps(msg)
    kafka_producer = topic.get_sync_producer()
    kafka_producer.produce(msg_str.encode('utf-8'))

    logger.info("Produced event Team message with Team ID: {} and Trace ID: {}".format(body["team_id"], body["trace_id"]))

    return NoContent, 201

def playerStatistics(body):
    trace_id = uuid.uuid4()
    body['trace_id'] = str(trace_id)

    logger.info("Received Event Player Request with Player ID: {} and Trace ID: {}".format(body["player_id"], body["trace_id"]))

    # Create the Kafka message
    msg = {
        "type": "Player",
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": body  # Use the entire request body as the payload
    }
    msg_str = json.dumps(msg)

    # Produce the Kafka message
    kafka_producer = topic.get_sync_producer()
    kafka_producer.produce(msg_str.encode('utf-8'))

    logger.info("Produced event Player message with Player ID: {} and Trace ID: {}".format(body["player_id"], body["trace_id"]))

    # Respond with a status code of 201 (Created)
    return NoContent, 201

def health():
    return jsonify({"status": "healthy"}), 200

app = connexion.FlaskApp(__name__, specification_dir='')

app.add_api("SoccerStats.yaml", strict_validation=True, validate_responses=True, base_path="/receiver")


if __name__ == '__main__':
    app.run(port=8080)