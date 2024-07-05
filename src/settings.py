"""
This file checks for the existence of a .env file and loads the environment variables from it. If the .env
file does not exist then we load the environment variables from the system environment variables.
"""

import os
from dotenv import load_dotenv
import logging
import openai
from pymongo import MongoClient


env_file = '../.env'
if os.path.exists(env_file):
    load_dotenv(dotenv_path=env_file)

# Configure the logging system
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler()]
)

# Suppress openai logging
if logging.getLogger('httpx').isEnabledFor(logging.DEBUG):
    logging.getLogger('httpx').setLevel(logging.INFO)
else:
    logging.getLogger('httpx').setLevel(logging.WARNING)

# Suppress pika logging
if logging.getLogger('pika').isEnabledFor(logging.DEBUG):
    logging.getLogger('pika').setLevel(logging.INFO)
else:
    logging.getLogger('pika').setLevel(logging.WARNING)

# Load the environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MONGO_URL = os.getenv('MONGO_URL')
SYS_MODE = os.getenv('SYS_MODE')
AGENT_QUEUE = os.getenv('AGENT_QUEUE')
RMQ_URL = os.getenv('RMQ_URL')

# Set the OpenAI API key
openai.api_key = OPENAI_API_KEY

# Connect to the database
client = MongoClient(MONGO_URL)
DB = client.swarm

