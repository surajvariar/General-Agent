import requests

OLLAMA_MODEL_API="https://ollama.com/api/tags"

def fetch_supported_models()->list[str]:
    supported_models=[]
    response=requests.get(OLLAMA_MODEL_API)
    if response.status_code!=200:
        return supported_models
    else:
        models_data=response.json()
        supported_models=[model.get("name") for model in models_data.get("models",[]) if model.get("name","")!="" ]
    return supported_models