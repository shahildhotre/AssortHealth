from supabase import create_client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase = create_client(supabase_url, supabase_key)

def test_insert():
    
    # Example data to inser
    
    # Insert data into a table (replace 'your_table_name' with actual table name)
    response = supabase.table('AssortHealthChatHistory').insert({
        'created_at': "2025-03-17 12:00:00",
        'from': "Shahil",
        'call_logs': "Testing",
        'call_ID': "1234567890",
        'patient_info': {"name": "John Doe", "age": 30, "gender": "Male"}
    }).execute()
    
    print("Insertion successful!")
    print("Response:", response)
        
    

if __name__ == "__main__":
    test_insert()
