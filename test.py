import openai
import streamlit as st
from streamlit_chat import message
import pymongo
import re

# Set up the OpenAI API key
openai.api_key = "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"

# Set up the MongoDB connection
connection_string = "mongodb+srv://vamshidharabhishek2:MYbm9oPXJwExWFRN@onbording-details.ljvbg8m.mongodb.net/test"
client = pymongo.MongoClient(connection_string)
db = client['employee_db']
collection = db['employees']

def chat_with_gpt(prompt, memory):
    messages = memory + [{'role': 'user', 'content': prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    return response.choices[0].message['content'].strip()

def extract_details(response, current_step):
    if current_step == 'ask_name':
        name_pattern = re.compile(r'(?:my (?:full )?name is|i am|call me|name is|my name is)\s*([A-Za-z\s]+)', re.IGNORECASE)
        match = name_pattern.search(response)
        if match:
            name = match.group(1).strip()
            if name.lower() not in ["hi", "hello", "hey"]:
                return name, None, None

    if current_step == 'ask_age':
        age_pattern = re.compile(r'\b(\d{1,3})\s*(years? old|yrs? old|years? of age|yrs? of age)?', re.IGNORECASE)
        match = age_pattern.search(response)
        if match:
            return None, match.group(1).strip(), None

    if current_step == 'ask_place':
        place_pattern = re.compile(r'\b(?:in|from|i live in)\s*([\w\s]+)', re.IGNORECASE)
        match = place_pattern.search(response)
        if match:
            return None, None, match.group(1).strip()

    return None, None, None

st.set_page_config(page_title="Employee Details Chatbot", page_icon=":robot_face:")

if 'history' not in st.session_state:
    st.session_state['history'] = []
    st.session_state['memory'] = [{'role': 'system', 'content': 'You are a friendly assistant who will collect some basic information from the user. Start with a greeting, then ask for their name, age, and place in a conversational manner.'}]
    st.session_state['employee_details'] = {'name': '', 'age': '', 'place': ''}
    st.session_state['current_step'] = 'greeting'

st.title("Employee Details Chatbot")

st.sidebar.title("Employee Details Chatbot")
st.sidebar.write("You are a friendly assistant who will collect some basic information from the user. Start with a greeting, then ask for their name, age, and place in a conversational manner.")

for i, chat in enumerate(st.session_state.history):
    if i % 2 == 0:
        message(chat, is_user=True, key=f"user_{i}")
    else:
        message(chat, key=f"bot_{i}")

def submit():
    user_input = st.session_state.user_input
    st.session_state.history.append(user_input)
    print(f"User input: {user_input}")  # Debugging log

    if st.session_state['current_step'] == 'greeting':
        response = "Hello! How are you today?"
        st.session_state['current_step'] = 'ask_name'
    else:
        response = chat_with_gpt(user_input, st.session_state['memory'])

    st.session_state.history.append(response)
    print(f"GPT-3 response: {response}")  # Debugging log
    st.session_state['memory'].append({'role': 'user', 'content': user_input})
    st.session_state['memory'].append({'role': 'assistant', 'content': response})

    name, age, place = extract_details(user_input, st.session_state['current_step'])
    print(f"Extracted details - Name: {name}, Age: {age}, Place: {place}")  # Debugging log

    if name and not st.session_state['employee_details']['name']:
        st.session_state['employee_details']['name'] = name
        response = "Thank you! How old are you?"
        st.session_state['current_step'] = 'ask_age'
    elif age and not st.session_state['employee_details']['age']:
        st.session_state['employee_details']['age'] = age
        response = "Great! Where are you from?"
        st.session_state['current_step'] = 'ask_place'
    elif place and not st.session_state['employee_details']['place']:
        st.session_state['employee_details']['place'] = place
        response = "Thank you for providing your details!"
        st.session_state['current_step'] = 'done'

    if all(st.session_state['employee_details'].values()):
        try:
            result = collection.insert_one(st.session_state['employee_details'])
            st.success("Employee details saved to the database.")
            print(f"Employee details saved to the database with id: {result.inserted_id}")
            st.session_state['employee_details'] = {'name': '', 'age': '', 'place': ''}
            st.session_state['memory'] = [{'role': 'system', 'content': 'You are a friendly assistant who will collect some basic information from the user. Start with a greeting, then ask for their name, age, and place in a conversational manner.'}]
            st.session_state['current_step'] = 'greeting'
        except Exception as e:
            st.error(f"An error occurred: {e}")
            print(f"An error occurred: {e}")

    st.session_state.user_input = ""  # Clear the input field

# Display the input field
st.text_input("Your response:", key="user_input", on_change=submit, placeholder="Type your message here...")

if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "bye"]:
            break
        response = chat_with_gpt(user_input, st.session_state['memory'])
        print("Chatbot: ", response)
