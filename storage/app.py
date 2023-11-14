import connexion
import yaml
import logging, logging.config
import datetime
import json
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from team import Team
from player import Player
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
from sqlalchemy import and_
from pykafka.exceptions import KafkaException


with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


# Create and connect to the database
DB_ENGINE = create_engine(f'mysql+pymysql://'
                          f'{app_config["datastore"]["user"]}:'
                          f'{app_config["datastore"]["password"]}@'
                          f'{app_config["datastore"]["hostname"]}:'
                          f'{app_config["datastore"]["port"]}/'
                          f'{app_config["datastore"]["db"]}')
Base.metadata.create_all(bind=DB_ENGINE)
# Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


# def teamStatistics(body):
#     """ Receives a team statistics object """

#     session = DB_SESSION()

#     t = Team(body['team_id'],
#              body['team_name'],
#              body['goals'],
#              body['wins'],
#              body['losses'],
#              body['number_of_players'],
#              body['trace_id'])
#     logger.debug("Stored event Team request with Trace ID: {}".format(body['trace_id']))

#     session.add(t)
#     session.commit()
#     session.close()


def getTeamStatistics(timestamp, end_timestamp):

    results_list = []
    
    session = DB_SESSION()
    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    # Added an end timestamp so we can specify a range for querying data from the database
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    # Query the database for records where the creation date is within the specified range
    teamStatistics = session.query(Team).filter(
        and_(Team.date_created >= timestamp_datetime,
             Team.date_created < end_timestamp_datetime)
    )

    for stat in teamStatistics:
        results_list.append(stat.to_dict())

    session.close()
    logger.info("Query for Team Statistics reading after {} returns {} results".format(timestamp, len(results_list)))

    return results_list, 200


# def playerStatistics(body):
#     """ Receives a player statistics object """

#     session = DB_SESSION()

#     p = Player(body['player_id'],
#               body['team_id'],
#               body['first_name'],
#               body['last_name'],
#               body['goals'],
#               body['age'],
#               body['jersey_number'],
#               body['trace_id'])
#     logger.debug("Stored event Player request with Trace ID: {}".format(body['trace_id']))

#     session.add(p)
#     session.commit()
#     session.close()


def getPlayerStatistics(timestamp, end_timestamp):

    results_list = []
    
    session = DB_SESSION()
    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    # Added an end timestamp so we can specify a range for querying data from the database
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    # Query the database for records where the creation date is within the specified range
    playerStatistics = session.query(Player).filter(
        and_(Player.date_created >= timestamp_datetime,
             Player.date_created < end_timestamp_datetime)
    )

    for stat in playerStatistics:
        results_list.append(stat.to_dict())

    session.close()
    logger.info("Query for Player Statistics reading after {} returns {} results".format(timestamp, len(results_list)))

    return results_list, 200

def process_messages():
    """ Process event messages with retry logic for Kafka connection """
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
            # Attempt to access the Kafka topic
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
                return
            
    # Create a consumer on a consumer group that reads only new, uncommitted messages.
    consumer = topic.get_simple_consumer(consumer_group=b'event_group', reset_offset_on_start=False, auto_offset_reset=OffsetType.LATEST)

    # This is a blocking loop that waits for new messages
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        payload = msg["payload"]

        if msg["type"] == "Team":
            # Perform actions for event1, such as storing the payload in a database
            session = DB_SESSION()

            t = Team(payload['team_id'],
                    payload['team_name'],
                    payload['goals'],
                    payload['wins'],
                    payload['losses'],
                    payload['number_of_players'],
                    payload['trace_id'])
            logger.debug("Stored event Team request with Trace ID: {}".format(payload['trace_id']))

            session.add(t)
            session.commit()
            session.close()

        elif msg["type"] == "Player":
            # Perform actions for event2, such as storing the payload in a database
            session = DB_SESSION()

            p = Player(payload['player_id'],
                    payload['team_id'],
                    payload['first_name'],
                    payload['last_name'],
                    payload['goals'],
                    payload['age'],
                    payload['jersey_number'],
                    payload['trace_id'])
            logger.debug("Stored event Player request with Trace ID: {}".format(payload['trace_id']))

            session.add(p)
            session.commit()
            session.close()

        # Commit the new message as being read
        consumer.commit_offsets()

app = connexion.FlaskApp(__name__, specification_dir='')

app.add_api("SoccerStats.yaml", strict_validation=True, validate_responses=True)


if __name__ == '__main__':
    logger.info("Connecting to DB. Hostname:{}, Port:{}".format(app_config["datastore"]["hostname"],
                                                            app_config["datastore"]["port"]))
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8090)