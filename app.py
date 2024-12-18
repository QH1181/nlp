import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

genai.configure(api_key="AIzaSyApjjQc7BUbTbTog3W0pJlkzfdAJvvdlao")

st.set_page_config(layout="wide")
st.title("NLP Chatbot")

#Set default model to 1.5
if "model" not in st.session_state:
    st.session_state.model = genai.GenerativeModel("gemini-1.5-flash")

#Initialize messages if there is none 
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "user", "parts": "Hello"},
        {"role": "model", "parts": "Great to meet you. What would you like to know?"}
    ]

#Initialize chat if there is none 
if "chat" not in st.session_state:
    model = genai.GenerativeModel("gemini-1.5-flash")
    st.session_state.chat = model.start_chat(
        history=[
            {"role": "user", "parts": "Hello"},
            {"role": "model", "parts": "Great to meet you. What would you like to know?"},
        ]
    )

with st.sidebar:

    #Model Picker
    options = ["Gemini 1.5 Flash", "Gemini 1.5 Pro", "Gemini 2.0 Flash EXP"]
    selectedOption = st.selectbox("Model", options)

    #Update if there is changes to the model
    if selectedOption != st.session_state.model:
        st.session_state.model = selectedOption
        if selectedOption == "Gemini 1.5 Flash":
            model = genai.GenerativeModel("gemini-1.5-flash")
        elif selectedOption == "Gemini 1.5 Pro":
            model = genai.GenerativeModel("gemini-1.5-pro")
        else:
            model = genai.GenerativeModel("gemini-2.0-flash-exp")

        st.session_state.chat = model.start_chat(history=st.session_state.messages)

    #File Uploader
    with st.form("Form", border=False, clear_on_submit=True):
        uploadedFile = st.file_uploader("File Uploader", type=[".pdf", '.mp3', '.wav'], accept_multiple_files=False)
        submitted = st.form_submit_button("Submit")

    #When user press submit and have uploaded files
    if submitted:
        if not uploadedFile:
            st.error("No file uploaded.")
        elif uploadedFile.name.lower().endswith(".pdf"):
            pdf_reader = PdfReader(uploadedFile)
            textContent = ""

            for page in pdf_reader.pages:
                if page.extract_text() is not None:
                    textContent += page.extract_text() + "\n"

            chat = st.session_state.chat
            response = chat.send_message("PDF Upload:\n" + textContent)
            response = response.text

            st.session_state.messages.append({"role": "user", "parts": "PDF Upload"})
            st.session_state.messages.append({"role": "model", "parts": response})

        else:

            if uploadedFile.name.lower().endswith(".mp3"):
                mimeType = "audio/mpeg"
            else:
                mimeType = "audio/wav"
                
            chat = st.session_state.chat
            audioFile = genai.upload_file(uploadedFile, mime_type=mimeType)
            response = chat.send_message([audioFile, "Describe this audio clip"])
            response = response.text

            st.session_state.messages.append({"role": "user", "parts": "Audio Upload"})
            st.session_state.messages.append({"role": "model", "parts": response})

    htmlStyle = """
    <style>
        .stFormSubmitButton > button{
            width: 100%;
        }

        .stFileUploader > section > button{
            width: 100%;
        }

        .stFileUploader > label > div > p{
            font-size: 1.2em;
        }

        .stSelectbox > label > div > p{
            font-size: 1.5em;
            font-weight: bold;
        }
            
    </style>
    
    """
    st.markdown(htmlStyle, unsafe_allow_html=True)

if userInput:=st.chat_input("Message Chatbot"): 
    with st.chat_message("user"):
        st.markdown(userInput)

    chat = st.session_state.chat
    response = chat.send_message(userInput)
    response = response.text    

    with st.chat_message("model"):
        st.markdown(response)   

    st.session_state.messages.append({"role": "user", "parts": userInput})
    st.session_state.messages.append({"role": "model", "parts": response})

#Display all of the messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"])
