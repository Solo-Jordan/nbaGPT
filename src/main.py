from settings import logging, RMQ_URL, AGENT_QUEUE
from nba_analyst import nba_analyst
from db_tools import create_convo_doc

from pika import BlockingConnection, URLParameters
import json
import uuid


def listen_on_queue():
    # This is the callback that is called when a message is received on the agent's queue.
    def callback(ch, method, properties, body):
        logging.info(f"Received message: {body}")
        body = json.loads(body)

        # Create UUID for the main thread
        main_thread_id = str(uuid.uuid4())

        # Create the convo document in the DB
        create_convo_doc(main_thread_id)

        # Call the nba_analyst function
        response = nba_analyst(main_thread_id, body['message'])

        logging.info(f"Listening on queue: {AGENT_QUEUE}")

    parameters = URLParameters(url=RMQ_URL)
    connection = BlockingConnection(parameters)
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)

    channel.queue_declare(queue=AGENT_QUEUE)
    channel.basic_consume(queue=AGENT_QUEUE,
                          on_message_callback=callback,
                          auto_ack=True)

    logging.info(f"Listening on queue: {AGENT_QUEUE}")
    channel.start_consuming()


if __name__ == '__main__':
    listen_on_queue()
