import connexion
import yaml
import logging, logging.config
import datetime
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from team import Team
from player import Player
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread


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
Base.metadata.bind = DB_ENGINE
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


def getTeamStatistics(timestamp):

    results_list = []
    
    session = DB_SESSION()
    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    teamStatistics = session.query(Team).filter(Team.date_created >= timestamp_datetime)

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


def getPlayerStatistics(timestamp):

    results_list = []
    
    session = DB_SESSION()
    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    playerStatistics = session.query(Player).filter(Player.date_created >= timestamp_datetime)

    for stat in playerStatistics:
        results_list.append(stat.to_dict())

    session.close()
    logger.info("Query for Player Statistics reading after {} returns {} results".format(timestamp, len(results_list)))

    return results_list, 200

def process_messages():
    """ Process event messages """
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

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