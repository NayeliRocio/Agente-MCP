import os
from dotenv import load_dotenv
load_dotenv()

def setting(name: str, default: str = '') -> str:
    return os.getenv(name, default).strip()
