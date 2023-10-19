import connexion
import datetime
import json
import yaml
import logging, logging.config
import uuid

from connexion import NoContent
from pykafka import KafkaClient


with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

kafka_client = KafkaClient(hosts='%s:%d' % (app_config["events"]["hostname"], app_config["events"]["port"]))
kafka_topic = kafka_client.topics[str.encode(app_config["events"]["topic"])]
kafka_producer = kafka_topic.get_sync_producer()


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
    kafka_producer.produce(msg_str.encode('utf-8'))
    
    logger.info("Produced event Player message with Player ID: {} and Trace ID: {}".format(body["player_id"], body["trace_id"]))

    # Respond with a status code of 201 (Created)
    return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir='')

app.add_api("SoccerStats.yaml", strict_validation=True, validate_responses=True)


if __name__ == '__main__':
    app.run(port=8080)