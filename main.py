from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import google.genai as genai
import os
from dotenv import load_dotenv
from google.genai.types import Content, Part

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mongo_client = MongoClient("mongodb://localhost:27017")
mongo_client = MongoClient(api_key=os.getenv("MONGODB_URI"))
db = mongo_client["Area83"]
rooms_collection = db["rooms"]
packages_collection = db["packages"]


chat_history = []


class ChatRequest(BaseModel):
    message: str


def get_room_details():
    rooms = list(rooms_collection.find({}, {"_id": 0}))
    return "\n".join([f"{r['type']} - {r['description']} for ₹{r['price']}/night" for r in rooms])


def get_package_details():
    packages = list(packages_collection.find({}, {"_id": 0}))
    return "\n".join([f"{p['name']}: {p['details']} (₹{p['price']})" for p in packages])


@app.post("/chat")
async def chat_endpoint(chat: ChatRequest):
    user_message = chat.message
    chat_history.append({"role": "user", "parts": [user_message]})


    room_info = get_room_details()
    package_info = get_package_details()


    system_prompt = f"""
You are a friendly virtual assistant for a resort website.
Format your response in clean, readable plain text.
Use headings, paragraphs, and new lines instead of bullets or Markdown characters like '*', '**', or '-'.

If the user asks anything outside the context or asks something you are not aware of, reply with
"Please contact administrator for furthur enquiries."

Use the following details to help the user:

Rooms:
{room_info}

Packages:
{package_info}

FAQs:
Q. What is the opening and closing time of the resort?
A. The resort opens at 6 AM and closes at 9 PM.

Q. How do you get my consent?
A. When you provide us with personal information to complete a transaction, verify your credit card, place an order, arrange for a delivery or return a purchase, we imply that you consent to our collecting it and using it for that specific reason only. If we ask for your personal information for a secondary reason, like marketing, we will either ask you directly for your expressed consent, or provide you with an opportunity to say no.

Q. How do I withdraw my consent?
A. If after you opt-in, you change your mind, you may withdraw your consent for us to contact you, for the continued collection, use or disclosure of your information, at anytime, by contacting us at info@area83.in or mailing us at: #619 2nd main 1st stage Indiranagar Bangalore 560038

Assist the user accordingly as per the details above.
"""

    try:
        
        convo = [
            Content(role="model", parts=[Part(text=system_prompt)]),
        ]

        for message in chat_history:
            convo.append(Content(role=message["role"], parts=[Part(text=p) for p in message["parts"]]))

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=convo
        )
        reply = response.text

        chat_history.append({"role": "model", "parts": [reply]})
        return {"reply": reply}
    except Exception as e:
        return {"reply": f"Sorry, I'm unable to respond right now. Please try again later. {e}"}

# To Run
# uvicorn main:app --reload
