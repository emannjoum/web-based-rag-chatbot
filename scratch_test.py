import sys
import os
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, os.path.abspath("src"))

from chatbot.application.dependencies import DependencyContainer
from chatbot.application.chat_service import ChatService

def main():
    container = DependencyContainer.default()
    chat_service = ChatService(container)
    try:
        res = chat_service.handle_text_query(
            "Hello",
            [],
            None,
            "GPT-4o mini",
            "Serper",
            is_drug_profile=False
        )
        print("Success!", res.response)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
