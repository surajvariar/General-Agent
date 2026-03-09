import requests
import json
import os
import uuid
from datetime import datetime
import streamlit as st

OLLAMA_MODEL_API="https://ollama.com/api/tags"
PATH=os.path.join(os.getcwd(),"conversation.json")  

def fetch_supported_models()->list[str]:
    supported_models=[]
    if os.getenv("OLLAMA_API_KEY"):
        response=requests.get(OLLAMA_MODEL_API)
        if response.status_code!=200:
            return supported_models
        else:
            models_data=response.json()
            supported_models=[model.get("name") for model in models_data.get("models",[]) if model.get("name","")!="" ]
    elif os.getenv("OPENAI_API_KEY"):
        supported_models=["nvidia/nemotron-3-nano-30b-a3b:free","qwen/qwen3-vl-30b-a3b-thinking","qwen/qwen3-vl-235b-a22b-thinking","qwen/qwen3-next-80b-a3b-instruct:free","openai/gpt-oss-120b:free","openai/gpt-oss-20b:free","qwen/qwen3-235b-a22b-thinking-2507","qwen/qwen3-coder:free","google/gemma-3n-e2b-it:free","google/gemma-3n-e4b-it:free","qwen/qwen3-4b:free","mistralai/mistral-small-3.1-24b-instruct:free","meta-llama/llama-3.3-70b-instruct:free","meta-llama/llama-3.2-3b-instruct:free","nousresearch/hermes-3-llama-3.1-405b:free"]
    return supported_models

def _generate_title_from_first_ai_response(messages: list) -> str:
    if not messages or not isinstance(messages, list):
        return "Untitled"
    first_ai_response = None
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "assistant" and msg.get("content"):
            first_ai_response = msg.get("content", "").strip()
            break
    if not first_ai_response:
        return "Untitled"
    words = first_ai_response.split()
    
    if len(words) <= 10:
        return " ".join(words)
    else:
        return " ".join(words[:10]) + "..."


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
    
    if session_id not in chat_history:
        title = _generate_title_from_first_ai_response(chat_data)
        chat_history[session_id] = {
            "title": title,
            "messages": chat_data,
            "updated_at": current_timestamp
        }
    else:
        if chat_history[session_id].get("title") == "Untitled" or not chat_history[session_id].get("title"):
            chat_history[session_id]["title"] = _generate_title_from_first_ai_response(chat_data)
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