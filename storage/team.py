from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


# Ceate class Team based on the object 'base'
class Team(Base):
    """ Team Statistics """

    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    team_id = Column(String(250), nullable=False)
    team_name = Column(String(250), nullable=False)
    goals = Column(Integer, nullable=False, default=0)
    wins = Column(Integer, nullable=False, default=0)
    losses = Column(Integer, nullable=False, default=0)
    number_of_players = Column(Integer, nullable=False, default=0)
    date_created = Column(String(250), nullable=False)
    trace_id = Column(String(250), nullable=False)

    # Constructor, whenever we call this class and pass different values
    # This will automatically assign the passed in values to what is in this constructor
    def __init__(self, team_id, team_name, goals, wins, losses, number_of_players, trace_id):
        """ Initializes a Team Statistics Object """
        self.team_id = team_id
        self.team_name = team_name
        self.goals = goals
        self.wins = wins
        self.losses = losses
        self.number_of_players = number_of_players
        self.date_created = datetime.datetime.now() # Sets the date/time record is created
        self.trace_id = trace_id

    def to_dict(self):
        """ Dictionary Representation of Team Statistics """
        dict = {}
        dict['id'] = self.id
        dict['team_id'] = self.team_id
        dict['team_name'] = self.team_name
        dict['goals'] = self.goals
        dict['wins'] = self.wins
        dict['losses'] = self.losses
        dict['number_of_players'] = self.number_of_players
        dict['date_created'] = self.date_created
        dict['trace_id'] = self.trace_id

        return dict
