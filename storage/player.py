from sqlalchemy import Column, Integer, String, DateTime
from base import Base
import datetime


# Ceate class Player based on the object 'base'
class Player(Base):
    """ Player Statistics """

    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    player_id = Column(String(250), nullable=False)
    team_id = Column(String(250), nullable=False)
    first_name = Column(String(250), nullable=False)
    last_name = Column(String(250), nullable=False)
    goals = Column(Integer, nullable=False, default=0)
    age = Column(Integer, nullable=False)
    jersey_number = Column(Integer, nullable=False)
    date_created = Column(String, nullable=False)
    trace_id = Column(String, nullable=False)

    # Constructor, whenever we call this class and pass different values
    # This will automatically assign the passed in values to what is in this constructor
    def __init__(self, player_id, team_id, first_name, last_name, goals, age, jersey_number, trace_id):
        """ Initializes a Player Statistics Object """
        self.player_id = player_id
        self.team_id = team_id
        self.first_name = first_name
        self.last_name = last_name
        self.goals = goals
        self.age = age
        self.jersey_number = jersey_number
        self.date_created = datetime.datetime.now() # Sets the date/time record is created
        self.trace_id = trace_id

    def to_dict(self):
        """ Dictionary Representation of Player Statistics """
        dict = {}
        dict['id'] = self.id
        dict['player_id'] = self.player_id
        dict['team_id'] = self.team_id
        dict['first_name'] = self.first_name
        dict['last_name'] = self.last_name
        dict['goals'] = self.goals
        dict['age'] = self.age
        dict['jersey_number'] = self.jersey_number
        dict['date_created'] = self.date_created
        dict['trace_id'] = self.trace_id

        return dict
