import mysql.connector
import yaml

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Establish a connection to MySQL server
db_conn = mysql.connector.connect(host=f'{app_config["datastore"]["hostname"]}',
                                      user=f'{app_config["datastore"]["user"]}',
                                      password=f'{app_config["datastore"]["password"]}')

# Create a cursor object to execute SQL queries
db_cursor = db_conn.cursor()

# Create the 'events' database if it doesn't exist
db_cursor.execute("CREATE DATABASE IF NOT EXISTS events")

# Switch to the 'events' database
db_cursor.execute("USE events")

# Create the 'teams' table
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS teams
    (id INT NOT NULL AUTO_INCREMENT, 
     team_id VARCHAR(250) NOT NULL,
     team_name VARCHAR(250) NOT NULL,
     goals INTEGER NOT NULL DEFAULT 0,
     wins INTEGER NOT NULL DEFAULT 0,
     losses INTEGER NOT NULL DEFAULT 0,
     number_of_players INTEGER NOT NULL DEFAULT 0,
     date_created VARCHAR(100) NOT NULL,
     trace_id VARCHAR(100) NOT NULL,
     CONSTRAINT team_pk PRIMARY KEY (id))
''')

# Create the 'players' table
db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS players
    (id INT NOT NULL AUTO_INCREMENT, 
     player_id VARCHAR(250) NOT NULL,
     team_id VARCHAR(250) NOT NULL,
     first_name VARCHAR(250) NOT NULL,
     last_name VARCHAR(250) NOT NULL,
     goals INTEGER NOT NULL DEFAULT 0,
     age INTEGER NOT NULL,
     jersey_number INTEGER NOT NULL,
     date_created VARCHAR(100) NOT NULL,
     trace_id VARCHAR(100) NOT NULL,
     CONSTRAINT player_pk PRIMARY KEY (id))
''')

# Commit the changes and close the connection
db_conn.commit()
db_conn.close()
