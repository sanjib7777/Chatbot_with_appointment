from langchain_openai import OpenAI
import re
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

llm = OpenAI(model="gpt-4o-mini",temperature=0)

def validate_email(email):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def validate_phone(phone):
    return bool(re.match(r"^\+?\d{10,15}$", phone))

def extract_date_with_openai(user_input):
    llm = OpenAI(model="gpt-4o-mini", temperature=0)
    prompt = f""" Today's date is {datetime.now().strftime("%Y-%m-%d")}. Now Convert the following natural language date to this format only: YYYY-MM-DD.
Just return the date only. Input: "{user_input}"."""

    response = llm.invoke(prompt).strip()

    
    match = re.search(r"\d{4}-\d{2}-\d{2}", response)
    if not match:
        print("⚠️ Unexpected format from LLM:", response)
        return None

    try:
        date_obj = datetime.strptime(match.group(), "%Y-%m-%d")
        return date_obj.strftime("%d %B %Y")  
    except ValueError:
        print("⚠️ Failed to parse extracted date:", match.group())
        return None
    

def book_appointment_tool(user_data):
    print("Booking appointment for:", user_data)
    return f"✅ Appointment booked for {user_data['name']} on {user_data['date']}"

from langchain.agents import Tool

def get_tools():
    return [
        Tool(
            name="BookAppointment",
            func=lambda x: book_appointment_tool(eval(x)),
            description="Tool for booking appointment with user data like name, email, date"
        )
    ]


print(extract_date_with_openai('next Monday'))  