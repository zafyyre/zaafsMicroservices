import mysql.connector
import yaml

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Establish a connection to MySQL server
db_conn = mysql.connector.connect(host=f'{app_config["datastore"]["hostname"]}', 
                                  user=f'{app_config["datastore"]["user"]}', 
                                  password=f'{app_config["datastore"]["password"]}',
                                  port=f'{app_config["datastore"]["port"]}')

# Create a cursor object to execute SQL queries
db_cursor = db_conn.cursor()

# Use the 'events' database
db_cursor.execute("USE events")

# Drop the 'teams' and 'players' tables if they exist
db_cursor.execute('''
    DROP TABLE IF EXISTS teams, players
''')

# Drop the 'events' database if it exists
db_cursor.execute('''
    DROP DATABASE IF EXISTS events
''')

# Commit the changes (in this case, dropping the tables and the database)
db_conn.commit()

# Close the cursor and the database connection
db_cursor.close()
db_conn.close()
