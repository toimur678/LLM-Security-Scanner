# Testing google api key if it's works for not.



import os
from langchain_community.chat_models import ChatGooglePalm
from langchain_core.messages import HumanMessage

# --- REPLACE WITH YOUR ACTUAL GOOGLE API KEY ---
api_key = "Your Google APIkey"
os.environ["GOOGLE_API_KEY"] = api_key

# --- TRY THIS MODEL NAME FIRST ---
model_to_test = "models/chat-bison-001"

print(f"Attempting to use model: {model_to_test} with ChatGooglePalm")
print(f"Using API Key: {api_key[:5]}...{api_key[-5:]}") # Print partial key for verification

try:
    chat = ChatGooglePalm(model_name=model_to_test)
    message = HumanMessage(content="Hello, PaLM model!")
    response = chat.invoke([message])
    print("--- API Call Successful ---")
    print("Response from model:")
    print(response.content)
except Exception as e:
    print(f"--- API Call Failed ---")
    print(f"An error occurred: {e}")
    print("\nTroubleshooting tips:")
    print("1. Ensure your GOOGLE_API_KEY is correct and for the right project.")
    print(f"2. Ensure the 'Generative Language API' is enabled in your Google Cloud project: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'PROJECT_ID_NOT_SET_IN_ENV')}")
    print(f"3. Verify that your API key has permissions to use the model '{model_to_test}' via the Generative Language API.")
    print("4. If using a Gemini key, it might not have default access to PaLM models via this specific Langchain class (ChatGooglePalm).")