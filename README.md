# nbaGPT

A custom GPT to discuss all things NBA.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)

## Introduction

nbaGPT is a specialized GPT model designed to engage in discussions about the NBA. It leverages advanced natural language processing techniques to provide insightful and engaging conversations about basketball.

## Installation

To get started with nbaGPT, clone the repository and install the necessary dependencies:

```bash
git clone <repository-url>
cd nbaGPT
pip install -r requirements.txt
```

## Environment Variables

Before running the application, create a `.env` file in the root directory with the following environment variables:

```
OPENAI_API_KEY=<your_openai_api_key>
MONGO_URL=<your_mongo_url>
SYS_MODE=<system_mode>
AGENT_QUEUE=<agent_queue_name>
RMQ_URL=<rabbitmq_url>
```

Replace the placeholders with your actual configuration values.

## Usage

To run nbaGPT, execute the following command:

```bash
python src/main.py
```

This will start the application, and you can begin interacting with the model.

## Project Structure

- `src/main.py`: The main entry point for the application.
- `src/agents/`: Contains agent-related classes and functions.
- `src/agent_tools/`: Tools and utilities for agent operations.
- `src/db_tools.py`: Database interaction functions.
- `src/settings.py`: Configuration settings for the application.
- `requirements.txt`: Lists the Python dependencies for the project.


