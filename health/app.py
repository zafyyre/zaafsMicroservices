import os
import logging.config
import yaml
import requests
import threading
import time
from flask_cors import CORS
import connexion
from flask import jsonify

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    APP_CONF_FILE = "/config/app_conf.yml"
    LOG_CONF_FILE = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    APP_CONF_FILE = "app_conf.yml"
    LOG_CONF_FILE = "log_conf.yml"

with open(APP_CONF_FILE, 'r', encoding='utf-8') as f:
    app_config = yaml.safe_load(f.read())

with open(LOG_CONF_FILE, 'r', encoding='utf-8') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')
logger.info(f"App Conf File: {APP_CONF_FILE}")
logger.info(f"Log Conf File: {LOG_CONF_FILE}")

service_statuses = {}

def getHealth():
    while True:
        for service_name, url in app_config['health_check']['services'].items():
            status = 'down'
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    status = 'running'
            except requests.exceptions.RequestException:
                pass

            service_statuses[service_name] = {
                'status': status,
                'last_checked': time.strftime('%Y-%m-%d %H:%M:%S')
            }

        time.sleep(app_config['health_check']['interval'])

def health():
    return jsonify(service_statuses)

app = connexion.FlaskApp(__name__, specification_dir='')

if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'

app.add_api("SoccerStats.yaml",
            strict_validation=True,
            validate_responses=True)

threading.Thread(target=getHealth, daemon=True).start()

if __name__ == '__main__':
    app.run(port=8120)
