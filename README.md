# AssortHealth

Take Home Assignment for AssortHealth - Call Center App 

Project is Deployed and Live

# Call: +1 6018084691
# UI: https://assort-health-takehome-shahil.vercel.app/

Tech Stack


| Component | Technologies |
|-----------|-------------|
| Frontend  | Next.js, TailwindCSS |
| Backend   | Python, Supabase (PostgreSQL) |
| LLMs      | OpenAI - STT, gpt-4o-mini, TTS |
| Agent     | LiveKit - VoicePipelineAgent |
| Phone     | Twilio |


#To run the project:

1. Clone the repository 

    git clone https://github.com/shahildhotre/AssortHealth.git

2. Install the dependencies

        cd AssortHealth
   
        pip install -r requirements.txt

4. Run the backend project

    add API keys in .env file
   
        python LiveKit-Twilio.py

   check if inbound_trunk json is updated with the right Twilio phone number
    
        python voiceAgent.py dev

6. Run the frontend project

        cd callcenterapp
   
        npm run dev

Demo Link: https://www.loom.com/share/6af19509c6b24cc6859c726747dc820e?sid=03219ace-bcf7-4b38-a90a-81d9aae48b40



