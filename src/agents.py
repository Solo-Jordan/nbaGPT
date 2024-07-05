from settings import logging, openai, DB, SYS_MODE

import time
import json


class Agent:
    """
    The Agent class. This class is used to create an agent that can be used to interact with the LLM. For now it is just
    using OpenAI but will be expanded to include Anthropic and Google.
    """
    def __init__(
            self,
            name: str,
            instructions: str,
            model: str,
            tools: list,
            main_thread_id: str,
            function_map: dict = None
    ):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools
        self.main_thread_id = main_thread_id
        self.function_map = function_map

        self.client = openai.OpenAI()
        self.id = self.create_assistant()
        self.thread_id = self.create_thread()

        self.response_msg = None

    def create_assistant(self) -> str:
        """
        Create the assistant.
        :return: The assistant.
        """

        assistant = self.client.beta.assistants.create(
            name=self.name,
            instructions=self.instructions,
            tools=self.tools,
            model=self.model
        )

        return assistant.id

    def create_thread(self) -> str:
        """
        Create a thread.
        :return: The thread.
        """

        thread = self.client.beta.threads.create()

        return thread.id

    def add_to_convo(self, response_msg: str | list, msg_type: str, from_agent: str, to_agent: str = None) -> bool:
        """
        Add a message to the conversation in the database.
        :param response_msg: The message to add.
        :param msg_type: The type of message to add.
        :param from_agent: The agent that the message is from.
        :param to_agent: The agent that the message is to.
        :return:
        """

        msg_dict = {
            "message": response_msg,
            "from_agent": from_agent,
            "to_agent": self.name if to_agent is None else to_agent,
            "msg_type": msg_type
        }

        convos = DB['swarm_convos']

        logging.info("Adding to convo in DB.")

        # If the system is in testing mode, then don't add to the DB.
        if SYS_MODE == "testing":
            logging.info("Mode is testing. Not adding to convo.")
            return True

        try:
            convos.update_one(
                {"id": self.main_thread_id},
                {
                    "$push": {
                        "convo": msg_dict
                    }
                }
            )
        except Exception as e:
            logging.error(f"Failed to add to convo. Error: {e}")
            return False

        return True

    def add_message(self, message: str) -> None:
        """
        Add a message to the thread.
        :param message: The message to add.
        :return: None
        """

        logging.info(f"Adding message to thread.")

        self.client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content=message
        )

        self.add_to_convo(response_msg=message, msg_type="message", from_agent="system")

        return

    def get_message_content(self) -> str:
        """
        Get the content of a message after a run.
        :return: The content of the message sent by the assistant.
        """
        # Get the message from the thread
        messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
        response_msg = None
        for message in messages:
            if message.assistant_id == self.id:
                for response in message.content:
                    if response.type == "text":
                        logging.info(f"Message ({self.thread_id}): {response.text.value}")
                        response_msg = response.text.value
                return response_msg

    def do_run(self) -> str:
        """
        Create a run in a thread.
        :return:
        """

        logging.info(f"Call to do run in thread: {self.thread_id}")

        # Have the assistant respond to the message in the thread by creating a run
        run = openai.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=self.id
        )

        # Wait for the run to complete
        status = run.status
        logging.info(f"Polling run: {run.id}")
        while run.status != 'completed':
            if run.status != status:
                status = run.status
            time.sleep(3)
            run = openai.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run.id
            )

            if run.status == 'requires_action':
                required_action = run.required_action.submit_tool_outputs.tool_calls
                logging.info(f"Tools request: {required_action}")
                # Add the function call to the convo in the database
                self.add_to_convo(response_msg=required_action, msg_type="function_call", from_agent=self.name)
                tools_output = []
                for action in required_action:
                    func_name = action.function.name
                    arguements = json.loads(action.function.arguments)
                    try:
                        # This is where we call the function with the arguments
                        output = self.function_map[func_name](**arguements)
                        logging.info(f"Function {func_name} successful. Response to assistant: {output}")
                    except TypeError as e:
                        if 'multi_tool_use.parallel' in str(e):
                            # Sometimes the assistant will hallucinate and call parallel fucntions with
                            # 'multi_tool_use.parallel' in the name. If this happens we need to send back an error and
                            # tell the assistant to try again.
                            logging.info(
                                f"Received 'multi_tool_use.parallel' hallucination. Sending error to assistant.")
                            message = "Please ignore any 'multi_tool_use.parallel' functions. They are not real. " \
                                      "Simply send the functions in an array. Please try again."
                            output = json.dumps({"status": "error", "msg": message})
                        else:
                            output = json.dumps({"status": "error", "msg": "Function not found."})
                            logging.error(f"Function {func_name} failed. Response to assistant: {output}")
                            logging.error(f"Error: {e}")

                    tools_output.append(
                        {
                            "tool_call_id": action.id,
                            "output": output
                        }
                    )

                logging.info(f"Adding Func responses to DB.")
                self.add_to_convo(response_msg=tools_output, msg_type="function_response", from_agent=self.name)
                logging.info(f"Submitting output to run.")
                run = openai.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.thread_id,
                    run_id=run.id,
                    tool_outputs=tools_output
                )

            elif run.status == 'completed':

                # Get the assistant's messages. The assistant's messages are the first messages in the list
                logging.info(f"This is the assistant's message on the thread that started this do_run.")
                response_msg = self.get_message_content()

                # Add the message to the convo in the database
                self.add_to_convo(response_msg, msg_type="message", from_agent=self.name, to_agent="system")

                # Set the response message to the response message from the assistant. I'm doing this in case I want to
                # access the last response message from the assistant anywhere else in the code.
                self.response_msg = response_msg

        return self.response_msg
