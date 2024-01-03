from settings import logging
from agent import Agent

logging.debug("Starting Agent.")

agent_name = input("What agent would you like to message? ")
agent = Agent(agent_name)
user_msg = input("What's your message?:\n")
print("\nStarting agent conversation. Type EXIT to exit.")

while user_msg != "EXIT":
    agent.add_user_msg(user_msg)
    agent_org_response = agent.do_run()
    agent.add_user_msg("Are you sure this is correct? Can you check this answer please?")
    agent_fin_response = agent.do_run()
    print(f"Agent: {agent_fin_response}\n")
    user_msg = input("RESPONSE (type 'EXIT' to exit):\n")

print("\nExiting.")
agent.delete_assistant()
print("Assistant deleted. Shutting down.")
