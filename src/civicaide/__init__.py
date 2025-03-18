# CivicAide package initialization 

from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from local.env in the src/civicaide directory
dotenv_path = Path(__file__).parent / "local.env"
load_dotenv(dotenv_path) 