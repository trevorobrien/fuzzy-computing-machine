# Solar Panel Savings Calculator Agent

This project implements an AI agent using LangGraph to calculate potential energy savings for solar panels. The agent serves as a lead generation tool for solar panel sellers, helping to qualify leads and provide personalized savings estimates.

## Features

- Interactive conversation flow to gather customer information
- Calculation of potential solar panel savings
- Lead qualification based on customer responses
- Personalized recommendations
- Data collection for sales team follow-up

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## Usage

The agent will interact with users to gather the following information:

- Monthly electricity costs
- Roof space availability
- Location/region
- Current energy consumption patterns
- Interest in solar panel installation

Based on this information, the agent will:

1. Calculate potential savings
2. Provide personalized recommendations
3. Qualify the lead
4. Generate a summary for the sales team

## Project Structure

- `main.py`: Main application entry point
- `agent.py`: LangGraph agent implementation
- `config.py`: Configuration settings
- `models.py`: Data models and schemas
- `utils.py`: Utility functions for calculations
