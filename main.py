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
mongo_client = MongoClient(os.getenv("MONGODB_URI"))
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

General FAQs
1. What is Area 83?
Area 83 is a premier adventure resort located on the outskirts of Bengaluru, offering a wide range of outdoor activities, stay options, and nature experiences.

2. Where is Area 83 located?
We are located at:
Bannerghatta Road, Bengaluru, Karnataka 560038
(Activities are conducted on our resort premises outside the city.)

3. What are your timings?
We are open from 9:00 AM to 6:00 PM for day visits. Overnight stays have flexible check-in/check-out times.

4. Is prior booking required?
Yes, prior booking is highly recommended for all experiences to ensure availability.

Activities & Packages
5. What kind of activities are available?
We offer a wide range of activities including:

Paintball
ATV rides
Kayaking
Ziplining
Obstacle courses
Human foosball
and more!

6. Are the activities safe?
Absolutely! All our activities are supervised by trained professionals with safety gear and precautions in place.

7. Can kids participate in the activities?
Yes, we have age-appropriate activities and separate kids' zones.

Booking & Payments
8. How can I book a visit?
You can book online through our website or contact us via WhatsApp or phone for assistance.

9. What are the payment options?
We accept UPI, debit/credit cards, net banking, and cash payments at the venue.

10. Is there a cancellation policy?
Yes. Cancellations made 48 hours prior to your visit are eligible for a refund. For full terms, refer to our cancellation policy on the website.

Accommodation
11. Do you offer overnight stays?
Yes, we have a variety of stay options including glamping tents and cottages.

12. Are meals included in stay packages?
Yes, most stay packages include meals. You can choose from vegetarian and non-vegetarian options.

Corporate & Group Events
13. Can you host corporate outings or team-building events?
Yes! We specialize in curated experiences for corporates, schools, and large groups.

14. Do you offer custom packages for groups?
Yes, our team will help tailor a package based on your group size and preferences.

Other Services
15. Is there parking available?
Yes, we offer free and secure parking on the premises.

16. Are pets allowed?
Currently, pets are not allowed for safety and hygiene reasons.

17. Is the resort wheelchair accessible?
We are working on making more areas accessible. Please call ahead for specific assistance.

18. How do I get to your resort?
Take a right turn at the Koli Farm Gate after the NICE Road junction on Bannerghatta Road. Then keep left from the gate — Area 83 is less than 1 km from there
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
