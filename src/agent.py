from settings import logging, openai
from nba_funcs import funcs
import time
import json
import os


class Agent:
    def __init__(self, asst: str):
        self.asst = asst

        # Load assistant from json file
        self.asst_file = os.path.join(os.path.dirname(__file__), "assistants.json")
        with open(self.asst_file, "r") as f:
            self.assistants = json.load(f)

        # Get the assistant
        self.asstistant_config = self.assistants["assistants"][self.asst]
        logging.debug(f"Assistant: {self.asstistant_config['name']}")

        self.assistant_id = self.create_assistant()
        self.thread_id = self.create_thread()

    def create_assistant(self):
        """
        Create an assistant.
        :return: The assistant ID.
        """
        tools = [self.assistants["functions"][tool] for tool in self.asstistant_config["tools"]]

        assistant = openai.beta.assistants.create(
            instructions=self.asstistant_config["instructions"],
            name=self.asstistant_config["name"],
            tools=tools,
            model=self.asstistant_config["model"],
        )
        logging.debug(f"Assistant created: {assistant.id}")

        return assistant.id

    def delete_assistant(self):
        """
        Delete an assistant.
        :return: The assistant ID.
        """
        openai.beta.assistants.delete(
            assistant_id=self.assistant_id
        )
        logging.debug(f"Assistant deleted: {self.assistant_id}")

        return

    @staticmethod
    def create_thread():
        """
        Create a thread.
        :return: The thread ID.
        """
        # Create the thread/chat
        thread = openai.OpenAI().beta.threads.create()
        logging.debug(f"Thread ID: {thread.id}")

        return thread.id

    def add_user_msg(self, msg: str = None) -> None:
        """
        Add a message to the thread.
        :param msg: The message.
        :return:
        """

        openai.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=msg
        )
        logging.debug("User message added to the thread.")

        return

    @staticmethod
    def get_message_content(run) -> str:
        """
        Get the content of a message after a run.
        :param run: An openai run object.
        :return: The content of the message sent by the assistant.
        """
        # Get the message from the thread
        messages = openai.beta.threads.messages.list(thread_id=run.thread_id)
        response_msg = None
        for message in messages:
            if message.assistant_id == run.assistant_id:
                for response in message.content:
                    if response.type == "text":
                        response_msg = response.text.value
                return response_msg

    def do_run(self):
        # Have the assistant respond to the message in the thread by creating a run
        logging.debug(f"Call to do run in thread: {self.thread_id}")
        run = openai.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.assistant_id
        )
        logging.debug(f"Run ID: {run.id}")

        response_msg = None  # This is to make the IDE happy
        # Wait for the run to complete
        while run.status != 'completed':
            logging.debug(f"Run status: {run.status}")
            time.sleep(3)
            logging.debug(f"Retrieving run again: {run.id}")
            run = openai.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run.id
            )

            if run.status == 'requires_action':
                required_action = run.required_action.submit_tool_outputs.tool_calls
                logging.debug(f"Tools request: {required_action}")
                tools_output = []
                for action in required_action:
                    func_name = action.function.name
                    arguements = json.loads(action.function.arguments)
                    try:
                        # This is where we call the function with the arguments
                        output = funcs[func_name](**arguements)
                        logging.debug(f"Function {func_name} successful. Response to assistant: {output}")
                    except TypeError:
                        output = json.dumps({"status": "error", "msg": "Function not found."})
                        logging.error(f"Function {func_name} failed. Response to assistant: {output}")

                    tools_output.append(
                        {
                            "tool_call_id": action.id,
                            "output": output
                        }
                    )

                run = openai.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.thread_id,
                    run_id=run.id,
                    tool_outputs=tools_output
                )

            elif run.status == 'completed':

                # Get the assistant's messages. The assistant's messages are the first messages in the list
                logging.debug(f"This is the assistant's message on the thread that started this do_run.")
                response_msg = self.get_message_content(run)

        return response_msg
