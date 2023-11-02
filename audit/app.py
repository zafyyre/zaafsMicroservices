import connexion
import json
import yaml
import logging, logging.config

from connexion import NoContent
from pykafka import KafkaClient
from flask_cors import CORS, cross_origin


with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

kafka_client = KafkaClient(hosts='%s:%d' % (app_config["events"]["hostname"], app_config["events"]["port"]))
kafka_topic = kafka_client.topics[str.encode(app_config["events"]["topic"])]
kafka_producer = kafka_topic.get_sync_producer()



def getTeamStatistics(index):

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
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("SoccerStats.yaml", strict_validation=True, validate_responses=True)

if __name__ == '__main__':
    app.run(port=8110)