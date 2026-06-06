from fastapi import APIRouter, Request, HTTPException, Query
import os
from dotenv import load_dotenv
from fastapi.background import BackgroundTasks
from api.services.whatsapp_service import send_whatsapp_message
from main import run_agent

load_dotenv()
router = APIRouter()
MAX_MESSAGE_LENGTH = 2000  # Define a maximum message length to prevent abuse

@router.post("/webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    print(f"Received webhook data: {data}")
    background_tasks.add_task(proccess_whatsapp_message, data)
    return {"status": "received"}

async def proccess_whatsapp_message(data: dict):
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]

        if "messages" not in value:
            return
        
        messages = value.get("messages", [])

        if not messages:
            return
        
        message = messages[0]
        user_message = message["text"]["body"]
        from_number = message["from"]

        print(f"Received message from {from_number}: {user_message}")

        # Check message length
        if len(user_message) > MAX_MESSAGE_LENGTH:
            print("Message too long")
            send_whatsapp_message(to=from_number, body="Your message is too long. Please keep it under 2000 characters.")
            return
        
        response = await run_agent(user_message, from_number)
        send_whatsapp_message(to=from_number, body=response)

    except Exception as e:
        print(f"Error processing webhook: {e}")

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str,
    hub_challenge: str,
    hub_verify_token: str
):
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")  # Replace with your actual verify token
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    else:        return "Verification failed", 403