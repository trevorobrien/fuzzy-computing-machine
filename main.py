from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from agent import app as agent_app
from langchain_core.messages import HumanMessage, AIMessage
from models import AgentState, CustomerInfo, SavingsEstimate, LeadQualification

app = FastAPI(title="Solar Savings Calculator Agent")

# Store conversation state
conversation_states: Dict[str, AgentState] = {}

class Message(BaseModel):
    content: str
    type: str = "human"

class ChatRequest(BaseModel):
    messages: List[Message]
    session_id: str = "default"  # Add session_id to track conversations

class ChatResponse(BaseModel):
    response: str
    lead_qualified: Optional[bool] = None
    priority_level: Optional[str] = None
    qualification_score: Optional[float] = None

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Convert messages to LangChain format
        messages = [
            HumanMessage(content=m.content) if m.type == "human"
            else AIMessage(content=m.content)
            for m in request.messages
        ]
        
        # Get or initialize state for this session
        state = conversation_states.get(request.session_id, {
            "messages": [],
            "customer_info": None,
            "savings_estimate": None,
            "lead_qualification": None
        })
        
        # Update messages in state
        state["messages"] = messages
        
        # Run the agent
        result = agent_app.invoke(state)
        
        # Store the updated state
        conversation_states[request.session_id] = result
        
        # Get the last AI message
        last_message = next(
            (m.content for m in reversed(result["messages"]) 
             if isinstance(m, AIMessage)),
            "I apologize, but I'm having trouble processing your request."
        )
        
        # Safely get lead qualification data
        lead_qualification = result.get("lead_qualification")
        lead_qualified = lead_qualification.is_qualified if lead_qualification else None
        priority_level = lead_qualification.priority_level if lead_qualification else None
        qualification_score = lead_qualification.qualification_score if lead_qualification else None
        
        # Prepare response
        response = ChatResponse(
            response=last_message,
            lead_qualified=lead_qualified,
            priority_level=priority_level,
            qualification_score=qualification_score
        )
        
        return response
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Solar Savings Calculator Agent API",
        "endpoints": {
            "/chat": "POST - Chat with the agent",
            "/docs": "GET - API documentation"
        }
    } 