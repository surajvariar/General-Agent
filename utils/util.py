import requests
import json
import os
import uuid
import streamlit as st
from agent.deep_agent import Agents

OLLAMA_MODEL_API="https://ollama.com/api/tags"
PATH=os.path.join(os.getcwd(),"conversation.json")  

def fetch_supported_models()->list[str]:
    supported_models=[]
    response=requests.get(OLLAMA_MODEL_API)
    if response.status_code!=200:
        return supported_models
    else:
        models_data=response.json()
        supported_models=[model.get("name") for model in models_data.get("models",[]) if model.get("name","")!="" ]
    return supported_models

def store_conversation_history(session_id:str,chat_data: dict[str, str]):
    chat_history = {}
    try:
        with open(PATH, "r") as f:
            chat_history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Skipping and continuing")
    if chat_history.get(session_id):
        chat_history[session_id]["messages"]=chat_data
    else:
        title=generate_chat_title(chat_data)
        chat_history[session_id]={"title":title,"messages":chat_data}

    with open(PATH, "w") as f:
        json.dump(chat_history, f, indent=4)

def fetch_conversation_history(session_id:str)->dict[str,str]:
    chat_history={}
    if not os.path.exists(PATH):
        return chat_history
    try:
        with open(PATH,"r") as f:
            chat_data=json.load(f)
            if chat_data.get(session_id):
                chat_history=chat_data[session_id]
    except json.JSONDecodeError:
        return {}
    return chat_history

def generate_session_id()->str:
    return str(uuid.uuid4())

def generate_chat_title(messages: list[dict]) -> str:
    text = "\n".join(f"{m['role']}: {m['content'][:100]}" for m in messages[:4] if m.get('content'))
    if not text:
        return "New Chat"
    agent=Agents(model_name="gpt-oss:20b", temp=0.7)
    llm = agent._init_model()

    try:
        res = llm.invoke(f"Short title (max 7 words) for this chat:\n\n{text}\n\nTitle:")
        title = res.content.strip().removeprefix("Title:").strip('"“”')
        return title or "Chat"
    except Exception as e:
        print(e)
        return "Chat"
@st.cache_data(ttl=None)
def load_all_sessions()->list[str]:
    session_ids=[]
    try:
        with open(PATH,"r") as f:
            chat_history:dict=json.load(f)
            sessions=chat_history.keys()
            session_ids=[id for id in sessions]
    except FileExistsError:
        return session_ids
    return session_ids

def delete_session(session_id):
    with open(PATH,"r") as f:
        chat_data:dict=json.load(f)
    chat_data.pop(session_id)
    
    with open(PATH,"w")as f:
        json.dump(chat_data,f,indent=5)