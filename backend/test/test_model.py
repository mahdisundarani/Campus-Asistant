import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

def test_gemini_model():
    print("Initializing Gemini Model...")
    try:
        llm = ChatOpenAI(
            model="google/gemini-2.5-flash",
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
            temperature=0.0,
        )
        
        print("\nSending a test prompt: 'Hi, what is 2+2?'")
        response = llm.invoke([HumanMessage(content="Hi, what is 2+2?")])
        
        print("\n=== RESPONSE RECEIVED ===")
        print(response.content)
        print("=========================\n")
        print("SUCCESS! The model is authenticated and working perfectly.")
        
    except Exception as e:
        print("\n=== ERROR ===")
        print(f"Failed to connect to the model: {str(e)}")
        print("=============\n")

if __name__ == "__main__":
    test_gemini_model()
