import logging
import os
import re
import asyncio
from datetime import datetime
from typing import Literal, Annotated, Dict

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, silero
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client





load_dotenv()
# from livekit import rtc

  # This will load from .env by default
logger = logging.getLogger("voice-agent")

livekit_api_key = os.getenv("LIVEKIT_API_KEY")
if not livekit_api_key:
    raise ValueError("LIVEKIT_API_KEY not found in environment variables")

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL or SUPABASE_KEY not found in environment variables")
supabase: Client = create_client(supabase_url, supabase_key)

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

conversation_history = {}
conversation_history["call_ID"] = "NULL"
conversation_history["call_logs"] = []
conversation_history["patient_metadata"] = {"name": "NULL", "dob": "NULL", "insurance": "NULL", "referral": "NULL", "complaint": "NULL", "address": "NULL", "phone": "NULL", "email": "NULL"}
conversation_history["from"] = "NULL"

class MedicalIntakeAgent(llm.FunctionContext):

    def __init__(self):
        super().__init__()
        # Initialize patient metadata to track intake progress
        self.patient_metadata = {"name": "NULL", "dob": "NULL", "insurance": "NULL", "referral": "NULL", "complaint": "NULL", "address": "NULL", "phone": "NULL", "email": "NULL"}
        # Add flag to track if call should end
        self.call_complete = False
        # Add list of goodbye phrases
        self.goodbye_phrases = [
            "goodbye", "bye", "thank you bye", "thanks bye", "have a good day",
            "see you", "take care", "end call", "hang up"
        ]
    

    @llm.ai_callable()
    def get_patient_info(self, 
                name: Annotated[str, llm.TypeInfo(description="The name of the patient")],
                dob: Annotated[str, llm.TypeInfo(description="The date of birth of the patient")],
                insurance: Annotated[str, llm.TypeInfo(description="The insurance of the patient")],
                referral: Annotated[str, llm.TypeInfo(description="The referral of the patient")],
                complaint: Annotated[str, llm.TypeInfo(description="The complaint of the patient")],
                address: Annotated[str, llm.TypeInfo(description="The address of the patient")],
                phone: Annotated[str, llm.TypeInfo(description="The phone number of the patient")],
                email: Annotated[str, llm.TypeInfo(description="The email of the patient")]
        )->str: 

        """Call this function as soon as patient gives it name.Collects patient medical intake information."""
        
        self.patient_metadata["name"] = name
        self.patient_metadata["dob"] = dob
        self.patient_metadata["insurance"] = insurance
        self.patient_metadata["referral"] = referral
        self.patient_metadata["complaint"] = complaint
        self.patient_metadata["address"] = address
        self.patient_metadata["phone"] = phone
        self.patient_metadata["email"] = email

        conversation_history["patient_metadata"] = self.patient_metadata

        print("Patient metadata: ---------------- ", self.patient_metadata)
        return f"Thank you for providing the information. I have saved it. Now I will check if the doctor is available."
        

    @llm.ai_callable()
    def check_doctor_availability(self, patient_availability: Annotated[str, llm.TypeInfo(description= "Patient availability day and time")])->str:
        """Dummy method to simulate doctor availability"""
        return "Doctor Shahil is available for appointment during your requested time. Should I book the appointment?"
    
    @llm.ai_callable()
    def book_appointment(self) -> str:
        """Dummy method to simulate booking an appointment"""
        metadata_dict = self.patient_metadata
        
        if metadata_dict["email"] != "NULL":
            try:
                # SMTP Configuration
                smtp_server = "smtp.gmail.com"
                smtp_port = 587
                sender_email = os.getenv("EMAIL_ADDRESS")
                sender_password = os.getenv("EMAIL_PASSWORD")

                # Create message
                message = MIMEMultipart("alternative")
                message["Subject"] = "Appointment Confirmation - Shahil's Medical Office"
                message["From"] = "shahildhotre999@gmail.com"
                message["To"] = metadata_dict["email"]  # Send to patient's email
                
                email_html = f"""
                <h2>Appointment Confirmation - Shahil's Medical Office</h2>
                <p>Dear {metadata_dict['name']},</p>
                
                <p>Your appointment at Shahil's Medical Office has been confirmed.</p>
                
                <h3>Patient Details:</h3>
                <ul>
                    <li><strong>Name:</strong> {metadata_dict['name']}</li>
                    <li><strong>Date of Birth:</strong> {metadata_dict['dob']}</li>
                    <li><strong>Reason for Visit:</strong> {metadata_dict['complaint']}</li>
                </ul>
                
                <p>Please bring your insurance card and any relevant medical records.</p>
                
                <p>If you need to reschedule, please call us at our office number.</p>
                
                <p>Best regards,<br>
                Shahil's Medical Office</p>
                """
                
                html_part = MIMEText(email_html, "html")
                message.attach(html_part)

                # Send email
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.send_message(message)
                
                logger.info(f"Confirmation email sent to {metadata_dict['email']}")
            except Exception as e:
                logger.error(f"Failed to send confirmation email: {e}")
                
        # Signal that we should end the call
        self.call_complete = True
        return "Appointment booked successfully! I'll send you a confirmation email with all the details. Thank you for choosing Shahil's Medical Office. Goodbye!"
    
    @llm.ai_callable()
    def check_goodbye(self, message: str) -> bool:
        """Check if the message contains a goodbye phrase"""
        message = message.lower().strip()
        return any(phrase in message for phrase in self.goodbye_phrases)


async def entrypoint(ctx: JobContext):
    # Remove FastAPI initialization comment
    
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a medical office assistant responsible for booking appointments for patients. "
            "Before booking appointment, you need to collect the following information from patients: full name, date of birth, insurance details, "
            "referral information, chief complaint/reason for visit, address, phone number, and email. "
            "Use the get_patient_info function to save this information as soon as you have collected it. "
            "Be professional, courteous, and guide the conversation naturally to collect all required information. "
            "Use short and clear questions, and confirm information when received. "
            "After collecting all information, inform the patient about checking doctor availability."
            "After checking doctor availability, inform the patient about booking the appointment."
        ),
    )

    fnc_ctx = MedicalIntakeAgent()

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    agent = VoicePipelineAgent(
        stt=openai.STT(),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(),
        vad=ctx.proc.userdata["vad"],  
        min_endpointing_delay=1.0,
        max_endpointing_delay=3.0,
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx,
    )

    agent.start(ctx.room, participant)

    log_queue = asyncio.Queue()

    @agent.on("user_speech_committed")
    def on_user_speech_committed(message: llm.ChatMessage):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_queue.put_nowait(f"[{timestamp}] USER:\n{message}\n\n")
        
        # Save user message to Supabase
        conversation_history["call_ID"] = ctx.room.name
        conversation_history["call_logs"].append(f"[{timestamp}] USER:\n{message.content}\n\n")
        conversation_history["from"] = "user"

        print("\n" + "="*50)
        print("👤 User:", message)
        print("="*50 + "\n")
        logger.info(f"User said: {message}")


        
        # Check if user said goodbye
        if fnc_ctx.check_goodbye(str(message)):
            fnc_ctx.call_complete = True
            supabase.table('AssortHealthChatHistory').insert({
                "from": str(conversation_history["from"]),
                "call_logs": str(conversation_history["call_logs"]),
                "call_ID": str(conversation_history["call_ID"]),
                "patient_info": conversation_history["patient_metadata"],
            }).execute()
            logger.info("Call ended: User initiated goodbye")
            asyncio.create_task(agent.say("Thank you for calling Shahil's medical office. Have a great day!"))

    @agent.on("agent_speech_committed")
    def on_agent_speech_committed(message: llm.ChatMessage):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save agent message to Supabase
        conversation_history["call_logs"].append(f"[{timestamp}] AGENT:\n{message.content}\n\n")
        conversation_history["from"] = "agent"
        conversation_history["call_ID"] = ctx.room.name

        print("\n" + "="*50)
        print("🤖 Agent:", message)
        print("="*50 + "\n")
        logger.info(f"Agent said: {message}")
        log_queue.put_nowait(f"[{timestamp}] AGENT:\n{message.content}\n\n")
        
        # Check if we should end the call
        if fnc_ctx.call_complete:
            supabase.table('AssortHealthChatHistory').insert({
                "from": str(conversation_history["from"]),
                "call_logs": str(conversation_history["call_logs"]),
                "call_ID": str(conversation_history["call_ID"]),
                "patient_info": conversation_history["patient_metadata"],
            }).execute()

            logger.info("Disconnecting call after completion")
            asyncio.create_task(ctx.room.disconnect())


    async def finish_queue():
        log_queue.put_nowait(None)
        # await write_task

    ctx.add_shutdown_callback(finish_queue)

    # Update the initial greeting
    await agent.say(
        "Hello! Welcome to Shahil's medical office. How may I help you today?"
    )



if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,  # Add the prewarm function
            agent_name="inbound-agent",
        ),
    )
