import uuid

from firebase_admin import credentials, firestore, initialize_app


def init_firebase():
    cred = credentials.Certificate("app/config/db.json")
    initialize_app(cred)
    return firestore.client()

def register_model(db, model_data):
    model_id = str(uuid.uuid4())
    db.collection('models').document(model_id).set(model_data)
    return model_id

def main():
    db = init_firebase()
    
    models = [
   # Whisper Models (ASR)
   {
       "name": "openai/whisper-tiny",
       "model_type": "speech_recognition",
       "requirements": {"cpu_cores": 2, "ram_gb": 4, "storage_gb": 1, "gpu_memory_gb": 8},
       "specifications": {"parameters": "39M", "context_size": 30, "precision": "FP16"},
       "provider": "OpenAI"
   },
   {
       "name": "openai/whisper-base",
       "model_type": "speech_recognition", 
       "requirements": {"cpu_cores": 4, "ram_gb": 4, "storage_gb": 1, "gpu_memory_gb": 4},
       "specifications": {"parameters": "74M", "context_size": 30, "precision": "FP16"},
       "provider": "OpenAI"
   },
   {
       "name": "openai/whisper-small.en",
       "model_type": "speech_recognition",
       "requirements": {"cpu_cores": 4, "ram_gb": 4, "storage_gb": 1, "gpu_memory_gb": 4},
       "specifications": {"parameters": "244M", "context_size": 30, "precision": "FP16"},
       "provider": "OpenAI"
   },
   {
       "name": "openai/whisper-medium",
       "model_type": "speech_recognition",
       "requirements": {"cpu_cores": 4, "ram_gb": 8, "storage_gb": 1.5, "gpu_memory_gb": 8},
       "specifications": {"parameters": "769M", "context_size": 30, "precision": "FP16"},
       "provider": "OpenAI"
   },
   {
       "name": "openai/whisper-large",
       "model_type": "speech_recognition",
       "requirements": {"cpu_cores": 8, "ram_gb": 16, "storage_gb": 3, "gpu_memory_gb": 16},
       "specifications": {"parameters": "1.5B", "context_size": 30, "precision": "FP16"},
       "provider": "OpenAI"
   },
   {
       "name": "openai/whisper-large-v2",
       "model_type": "speech_recognition",
       "requirements": {"cpu_cores": 8, "ram_gb": 16, "storage_gb": 3, "gpu_memory_gb": 16},
       "specifications": {"parameters": "1.5B", "context_size": 30, "precision": "FP16"},
       "provider": "OpenAI"
   },
   {
       "name": "openai/whisper-large-v3",
       "model_type": "speech_recognition",
       "requirements": {"cpu_cores": 8, "ram_gb": 16, "storage_gb": 3, "gpu_memory_gb": 16},
       "specifications": {"parameters": "1.5B", "context_size": 30, "precision": "FP16"},
       "provider": "OpenAI"
   },
   {
       "name": "openai/whisper-large-v3-turbo",
       "model_type": "speech_recognition",
       "requirements": {"cpu_cores": 8, "ram_gb": 16, "storage_gb": 3, "gpu_memory_gb": 16},
       "specifications": {"parameters": "1.5B", "context_size": 30, "precision": "FP16"},
       "provider": "OpenAI"
   },

   # GPT Models
   {
       "name": "gpt2",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 4, "ram_gb": 8, "storage_gb": 1.5, "gpu_memory_gb": 4},
       "specifications": {"parameters": "124M", "context_size": 1024, "precision": "FP16"},
       "provider": "OpenAI"
   },
   {
       "name": "gpt2-medium",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 4, "ram_gb": 8, "storage_gb": 2, "gpu_memory_gb": 8},
       "specifications": {"parameters": "355M", "context_size": 1024, "precision": "FP16"},
       "provider": "OpenAI"
   },
   {
       "name": "gpt2-large",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 8, "ram_gb": 16, "storage_gb": 3, "gpu_memory_gb": 16},
       "specifications": {"parameters": "774M", "context_size": 1024, "precision": "FP16"},
       "provider": "OpenAI"
   },

   # DeepSeek Models
   {
       "name": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 8, "ram_gb": 16, "storage_gb": 14, "gpu_memory_gb": 16},
       "specifications": {"parameters": "7B", "context_size": 4096, "precision": "FP16"},
       "provider": "DeepSeek"
   },
   {
       "name": "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 16, "ram_gb": 32, "storage_gb": 28, "gpu_memory_gb": 32},
       "specifications": {"parameters": "14B", "context_size": 4096, "precision": "FP16"},
       "provider": "DeepSeek"
   },
   {
       "name": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 32, "ram_gb": 64, "storage_gb": 56, "gpu_memory_gb": 64},
       "specifications": {"parameters": "32B", "context_size": 4096, "precision": "FP16"},
       "provider": "DeepSeek"
   },
   {
       "name": "deepseek-ai/deepseek-coder-6.7b-instruct",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 8, "ram_gb": 16, "storage_gb": 14, "gpu_memory_gb": 16},
       "specifications": {"parameters": "6.7B", "context_size": 4096, "precision": "FP16"},
       "provider": "DeepSeek"
   },

   # OpenELM Models
   {
       "name": "apple/OpenELM-270M",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 4, "ram_gb": 8, "storage_gb": 1, "gpu_memory_gb": 8},
       "specifications": {"parameters": "270M", "context_size": 2048, "precision": "FP16"},
       "provider": "Apple"
   },
   {
       "name": "apple/OpenELM-450M",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 4, "ram_gb": 8, "storage_gb": 1.5, "gpu_memory_gb": 8},
       "specifications": {"parameters": "450M", "context_size": 2048, "precision": "FP16"},
       "provider": "Apple"
   },
   {
       "name": "apple/OpenELM-1.1B",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 4, "ram_gb": 8, "storage_gb": 3, "gpu_memory_gb": 8},
       "specifications": {"parameters": "1.1B", "context_size": 2048, "precision": "FP16"},
       "provider": "Apple"
   },
   {
       "name": "apple/OpenELM-3B",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 8, "ram_gb": 16, "storage_gb": 6, "gpu_memory_gb": 8},
       "specifications": {"parameters": "3B", "context_size": 2048, "precision": "FP16"},
       "provider": "Apple"
   },

   # Meta Models
   {
       "name": "meta-llama/Llama-3.2-1B",
       "model_type": "text_generation",
       "requirements": {"cpu_cores": 4, "ram_gb": 8, "storage_gb": 2, "gpu_memory_gb": 16},
       "specifications": {"parameters": "1.1B", "context_size": 2048, "precision": "FP16"},
       "provider": "Meta"
   },

   # Text to Speech Models
   {
       "name": "microsoft/speecht5_tts",
       "model_type": "text_to_speech",
       "requirements": {"cpu_cores": 8, "ram_gb": 16, "storage_gb": 8, "gpu_memory_gb": 16},
       "specifications": {"parameters": "760M", "context_size": 1024, "precision": "FP16"},
       "provider": "Microsoft"
   }
]
    
    for model in models:
        model_id = register_model(db, model)
        print(f"Registered {model['name']} with ID: {model_id}")

if __name__ == "__main__":
    main()