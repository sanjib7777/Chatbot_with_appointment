import streamlit as st
from chatbot_tools import validate_email, validate_phone, extract_date_with_openai, get_tools
from doc_chat import create_vector_store_from_documents, get_qa_chain
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import OpenAI
from langchain.agents import initialize_agent
from dotenv import load_dotenv

load_dotenv()


st.set_page_config(page_title=" AI Assistant", layout="centered")

# Cache setup of model to avoid reload on every rerun
@st.cache_resource
def setup_models():
    vector_store = create_vector_store_from_documents("sample.txt")
    qa_chain = get_qa_chain(vector_store)
    tools = get_tools()
    agent = initialize_agent(
        tools,
        OpenAI(model="gpt-4o-mini", temperature=0),
        agent="zero-shot-react-description",
        verbose=False,
    )
    memory = ConversationBufferMemory()
    convo = ConversationChain(llm=OpenAI(temperature=0), memory=memory)
    return qa_chain, agent, convo

qa_chain, agent, convo = setup_models()

st.title("AI Chatbot with Appointment Booking")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help you today?"}]

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# user input
if prompt := st.chat_input("Your message:"):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message containre
    with st.chat_message("user"):
        st.markdown(prompt)

    if "call me" in prompt.lower() or "book" in prompt.lower():
        
        st.session_state.show_booking_form = True

# Check if we need to show booking form 
if st.session_state.get("show_booking_form"):
    with st.chat_message("assistant"):
        with st.form("appointment_form"):
            st.markdown("Please provide your details for the appointment:")
            name = st.text_input("Your Name")
            email = st.text_input("Your Email")
            phone = st.text_input("Your Phone Number")
            date_input = st.text_input("Preferred Date (e.g., next Monday)")
            submitted = st.form_submit_button("Book Appointment")

            if submitted:
                if not validate_email(email):
                    st.error("Invalid Email")
                elif not validate_phone(phone):
                    st.error("Invalid Phone Number")
                else:
                    formatted_date = extract_date_with_openai(date_input)
                    if not formatted_date:
                        st.error("Couldn't understand the date. Please try something like 'next Sunday'")
                    else:
                        user_data = {
                            "name": name,
                            "email": email,
                            "phone": phone,
                            "date": formatted_date
                        }
                        with st.spinner("Booking appointment..."):
                            response = agent.run(str(user_data))
                        bot_msg = f"Appointment booked for **{formatted_date}**.\n\n**Response:** {response}"
                        # Add both the form and the response to history
                        st.session_state.messages.extend([
                            {"role": "assistant", "content": "Please provide your details for the appointment:"},
                            {"role": "user", "content": f"Name: {name}, Email: {email}, Phone: {phone}, Date: {date_input}"},
                            {"role": "assistant", "content": bot_msg}
                        ])
                        # Reset the form flag
                        st.session_state.show_booking_form = False
                        # Rerun to show updated chat
                        st.rerun()

# Handle non-booking messages
elif st.session_state.messages[-1]["role"] == "user" and not st.session_state.get("show_booking_form"):
    last_user_message = st.session_state.messages[-1]["content"]
    if not ("call me" in last_user_message.lower() or "book" in last_user_message.lower()):
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = qa_chain.run(last_user_message)
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})