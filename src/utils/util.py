import requests
import json
import os
import uuid
from datetime import datetime
import streamlit as st
from huggingface_hub import HfApi
from models.settings import settings

OLLAMA_MODEL_API="https://ollama.com/api/tags"
PATH=os.path.join(os.getcwd(),"conversation.json")  

def fetch_supported_models()->list[str]:
    supported_models=[]
    try:
        if settings.OLLAMA_API_KEY:
            response=requests.get(OLLAMA_MODEL_API)
            if response.status_code!=200:
                return supported_models
            else:
                models_data=response.json()
                supported_models=[model.get("name") for model in models_data.get("models",[]) if model.get("name","")!="" ]
        if settings.OPENAI_API_KEY:
            supported_models=settings.OPEN_ROUTER_MODELS
        if settings.HUGGINGFACEHUB_API_TOKEN:
            api = HfApi()
            models = api.list_models(sort="trending_score",limit=20,inference_provider="all")
            supported_models = [model.id for model in models]
    except Exception as e:
        print(e)
        supported_models=[]
    return supported_models

def _generate_title_from_first_ai_response(messages: list) -> str:
    """
    Generate a title from the first AI response in the conversation.
    If no AI response exists yet, generate a title from the first user message.
    """
    if not messages or not isinstance(messages, list):
        return "New Conversation"
    
    # Try to find the first AI response
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
            first_ai_response = msg.get("content", "").strip()
            if first_ai_response:
                words = first_ai_response.split()
                if len(words) <= 10:
                    return " ".join(words)
                else:
                    return " ".join(words[:10]) + "..."
    
    # If no AI response, try to use the first user message
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "user" and msg.get("content"):
            first_user_message = msg.get("content", "").strip()
            if first_user_message:
                words = first_user_message.split()
                if len(words) <= 5:
                    return " ".join(words)
                else:
                    return " ".join(words[:5]) + "..."
    
    return "New Conversation"


def store_conversation_history(session_id: str, chat_data: list):
    if not session_id or not isinstance(session_id, str):
        return
    
    if chat_data is None:
        chat_data = []
    
    if not isinstance(chat_data, list):
        return
    chat_history = {}
    try:
        with open(PATH, "r") as f:
            chat_history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        chat_history = {}
    except Exception as e:
        print(f"Error reading conversation history: {e}")
        chat_history = {}
    if not isinstance(chat_history, dict):
        chat_history = {}
    current_timestamp = datetime.now().isoformat()
    
    # Always update the conversation data
    title = _generate_title_from_first_ai_response(chat_data)
    if session_id not in chat_history:
        chat_history[session_id] = {
            "title": title,
            "messages": chat_data,
            "updated_at": current_timestamp
        }
    else:
        # Update title if it's a better one or if the previous was generic
        old_title = chat_history[session_id].get("title", "")
        if old_title in ["Untitled", "New Conversation"] and title not in ["Untitled", "New Conversation"]:
            chat_history[session_id]["title"] = title
        elif not old_title:
            chat_history[session_id]["title"] = title
            
        chat_history[session_id]["messages"] = chat_data
        chat_history[session_id]["updated_at"] = current_timestamp
        
    try:
        with open(PATH, "w") as f:
            json.dump(chat_history, f, indent=4)
    except Exception as e:
        print(f"Error saving conversation history: {e}")


def generate_session_id()->str:
    return str(uuid.uuid4())

@st.cache_data(ttl=None)
def load_all_sessions()->dict:
    """Load all sessions and return sorted by updated_at in descending order."""
    chat_history:dict={}
    try:
        with open(PATH,"r") as f:
            chat_history=json.load(f)
    except Exception as e:
        return chat_history
    
    sorted_history = dict(sorted(
        chat_history.items(),
        key=lambda item: item[1].get("updated_at", ""),
        reverse=True
    ))
    
    return sorted_history

def load_all_sessions_uncached()->dict:
    """Load all sessions without caching - for immediate updates."""
    chat_history:dict={}
    try:
        with open(PATH,"r") as f:
            chat_history=json.load(f)
    except Exception as e:
        return chat_history
    
    sorted_history = dict(sorted(
        chat_history.items(),
        key=lambda item: item[1].get("updated_at", ""),
        reverse=True
    ))
    
    return sorted_history

def delete_session(session_id):
    try:
        with open(PATH,"r") as f:
            chat_data:dict=json.load(f)
        if session_id in chat_data.keys():
            chat_data.pop(session_id)
        
        with open(PATH,"w")as f:
            json.dump(chat_data,f,indent=5)
    except Exception as e:
        raise e