from typing import Annotated, Sequence, TypedDict
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from models import AgentState, CustomerInfo, SavingsEstimate, LeadQualification
from utils import calculate_savings, qualify_lead
import json
from dotenv import load_dotenv
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
logger.info("Loading environment variables")

# Verify API key is loaded
if not os.getenv("OPENAI_API_KEY"):
    logger.error("OPENAI_API_KEY environment variable is not set")
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please check your .env file.")

# Define the state type
class AgentState(TypedDict):
    messages: Sequence[HumanMessage | AIMessage]
    customer_info: CustomerInfo | None
    savings_estimate: SavingsEstimate | None
    lead_qualification: LeadQualification | None

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4.1")

# Define the system prompt
SYSTEM_PROMPT = """You are a solar panel savings calculator agent. Your goal is to help potential customers understand their potential savings from solar panel installation while gathering information to qualify them as leads.

Follow these steps:
1. Greet the customer and explain your purpose
2. Gather necessary information:
   - Monthly electricity costs
   - Roof type and size
   - Location
   - Average daily sunlight
   - Interest in installation
3. Calculate potential savings
4. Present the results
5. Qualify the lead
6. Provide next steps

Be professional, informative, and focused on helping the customer understand their potential savings."""

def process_message(state: AgentState) -> AgentState:
    """Process the current message and determine the next action."""
    logger.info("Processing new message")
    messages = state["messages"]
    
    # If this is the first message, send greeting
    if len(messages) == 1 and isinstance(messages[0], HumanMessage):
        logger.info("First message detected, sending greeting")
        return {
            **state,
            "messages": [
                *messages,
                AIMessage(content="Hello! I'm your solar savings calculator assistant. I can help you understand how much you could save by installing solar panels. To get started, could you tell me your average monthly electricity bill?")
            ]
        }
    
    # If we already have customer info and savings estimate, move to summary
    if state.get("customer_info") and state.get("savings_estimate"):
        logger.info("Customer info and savings estimate found, moving to summary")
        return final_summary(state)
    
    # If we already have customer info, return the current state
    if state.get("customer_info"):
        logger.info("Customer info already exists, returning current state")
        return state
    
    # Get the last user message
    last_user_message = next((m.content for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    if not last_user_message:
        logger.warning("No user message found in the conversation")
        return state
    
    logger.info("Extracting information from user message")
    # Extract information from the conversation
    response = llm.invoke([
        HumanMessage(content=f"""You are a data extraction assistant. Extract the following information from the user's message and return it as a JSON object.
        Current message: {last_user_message}
        
        Extract these specific pieces of information:
        1. monthly_electricity_cost: Extract the number after $ symbol (e.g., if user says "$250 per month", extract 250.0)
        2. roof_size: Extract the number before "sq ft" (e.g., if user says "1500 sq ft", extract 1500.0)
        3. location: Extract the city/location name
        4. roof_type: Look for words "flat", "pitched", or "other"
        5. average_daily_sunlight: Use 4.0 as default
        6. interested_in_installation: Use true as default
        
        Return ONLY a JSON object in this exact format:
        {{
            "monthly_electricity_cost": 250.0,
            "roof_type": "pitched",
            "roof_size": 1500.0,
            "location": "san francisco",
            "average_daily_sunlight": 4.0,
            "interested_in_installation": true
        }}
        
        IMPORTANT: All numerical values must be floats, not strings or null.
        """)
    ])
    
    try:
        # Parse the response and create a dictionary with default values
        info_dict = json.loads(response.content)
        logger.info(f"Extracted information: {info_dict}")
        
        # Safely convert values to float with defaults
        def safe_float(value, default=0.0):
            if value is None:
                return default
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
        customer_info = CustomerInfo(
            monthly_electricity_cost=safe_float(info_dict.get("monthly_electricity_cost")),
            roof_type=info_dict.get("roof_type", "other"),
            roof_size=safe_float(info_dict.get("roof_size")),
            location=info_dict.get("location", "unknown"),
            average_daily_sunlight=safe_float(info_dict.get("average_daily_sunlight", 4.0)),
            interested_in_installation=bool(info_dict.get("interested_in_installation", True))
        )
        
        # Check if we have enough information to proceed
        missing_info = []
        if not customer_info.monthly_electricity_cost:
            missing_info.append("monthly electricity bill")
        if not customer_info.roof_size:
            missing_info.append("roof size")
        if customer_info.location == "unknown":
            missing_info.append("location")
        if customer_info.roof_type == "other":
            missing_info.append("roof type")
        
        if missing_info:
            logger.info(f"Missing information: {missing_info}")
            return {
                **state,
                "messages": [
                    *messages,
                    AIMessage(content=f"I see you've provided some information, but I still need a few more details to give you an accurate estimate. Could you please provide:\n" + 
                                    "\n".join(f"- {info}" for info in missing_info))
                ]
            }
        
        logger.info("Calculating savings and qualifying lead")
        # Calculate savings and qualify lead
        savings_estimate = calculate_savings(customer_info)
        lead_qualification = qualify_lead(customer_info, savings_estimate)
        
        logger.info(f"Savings estimate: {savings_estimate}")
        logger.info(f"Lead qualification: {lead_qualification}")
        
        return {
            **state,
            "customer_info": customer_info,
            "savings_estimate": savings_estimate,
            "lead_qualification": lead_qualification,
            "messages": [
                *messages,
                AIMessage(content=f"""Based on your information, here's what I've calculated:

Annual Savings: ${savings_estimate.annual_savings}
Payback Period: {savings_estimate.payback_period} years
Recommended System Size: {savings_estimate.recommended_system_size} kW
Estimated Installation Cost: ${savings_estimate.estimated_installation_cost}
Environmental Impact: {savings_estimate.environmental_impact} tons of CO2 reduction per year

Would you like to learn more about the installation process or have any questions about these estimates?""")
            ]
        }
    except Exception as e:
        logger.error(f"Error processing information: {str(e)}", exc_info=True)
        return {
            **state,
            "messages": [
                *messages,
                AIMessage(content="I need a bit more information to help you calculate your potential savings. Could you please provide:\n" +
                                "- Your monthly electricity bill (e.g., $1000)\n" +
                                "- Your roof size in square feet (e.g., 100 sq ft)\n" +
                                "- Your location (e.g., London)\n" +
                                "- What type of roof you have (flat, pitched, or other)")
            ]
        }

def final_summary(state: AgentState) -> AgentState:
    """Provide final summary and next steps."""
    logger.info("Generating final summary")
    if state.get("lead_qualification"):
        qualification = state["lead_qualification"]
        logger.info(f"Lead qualification status: {qualification.is_qualified}")
        return {
            **state,
            "messages": [
                *state["messages"],
                AIMessage(content=f"""Thank you for your interest in solar energy! Here's a summary of our discussion:

Lead Qualification: {'Qualified' if qualification.is_qualified else 'Not Qualified'}
Priority Level: {qualification.priority_level}
Qualification Score: {qualification.qualification_score}/100

Next Steps:
1. A solar energy specialist will review your information
2. You'll receive a detailed proposal within 24-48 hours
3. Schedule a free roof assessment
4. Discuss financing options

Would you like to provide your contact information for follow-up?""")
            ]
        }
    logger.warning("No lead qualification found in state")
    return state

# Create the graph
logger.info("Initializing workflow graph")
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("process", process_message)
workflow.add_node("summary", final_summary)

# Add edges
workflow.add_edge("process", "summary")

# Set entry point
workflow.set_entry_point("process")

# Compile the graph
logger.info("Compiling workflow graph")
app = workflow.compile()
logger.info("Application initialization complete") 