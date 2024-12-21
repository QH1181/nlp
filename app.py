import streamlit as st
from PyPDF2 import PdfReader
import shelve
import google.generativeai as genai
from gtts import gTTS
import pygame
import os
import nltk
from nltk.corpus import stopwords
import re
from groq import Groq
import speech_recognition as sr

genai.configure(api_key="AIzaSyApjjQc7BUbTbTog3W0pJlkzfdAJvvdlao")
client = Groq(api_key='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')
recognizer = sr.Recognizer()


def loadChatHistory():
    with shelve.open('chatHistory') as db:

        if 'messages' not in db:
            db['messages'] = [
                {"role": "user", "parts": "Hello"},
                {"role": "assistant", "parts": "Gemini 1.5 Flash : Great to meet you. What would you like to know?"}
            ]
        return db['messages']
    
def saveChatHistory():
    with shelve.open('chatHistory', writeback=True) as db:
        existingMessages = db.get('messages', [])
        newMessages = [msg for msg in st.session_state.messages if msg not in existingMessages]
        existingMessages.extend(newMessages)
        db['messages'] = existingMessages
        db.sync()


def textToSpeech(oriText, speechEnabled):
    if speechEnabled:
        if os.path.exists("temp.mp3"):
            pygame.mixer.quit()
            os.remove("temp.mp3")
        myobj = gTTS(text=oriText, lang='en', slow=False)
        myobj.save("temp.mp3")
        pygame.mixer.init()
        pygame.mixer.music.load("temp.mp3")
        pygame.mixer.music.play()

def removeStopWords(text):
    stop_words = set(stopwords.words('english'))
    words = re.findall(r'\b\w+\b', text)
    filtered_words = [word for word in words if word.lower() not in stop_words]
    return " ".join(filtered_words)

if 'messages' not in st.session_state:
    st.session_state.messages = loadChatHistory()

if 'model' not in st.session_state:
    st.session_state.model = genai.GenerativeModel("gemini-1.5-flash")

if 'modelName' not in st.session_state:
    st.session_state.modelName = "Gemini 1.5 Flash"

if 'chat' not in st.session_state:
    model = genai.GenerativeModel("gemini-1.5-flash")
    st.session_state.chat = model.start_chat(
        history=[
            {"role": "user", "parts": "Hello"},
            {"role": "assistant", "parts": "Gemini 1.5 Flash : Great to meet you. What would you like to know?"},
        ]
    )

if 'groqPrompt' not in st.session_state:
    st.session_state.groqPrompt = {"role": "system", "content": "You are a Large Language Model that do anything that is asked."}
    st.session_state.groqChatHistory = [st.session_state.groqPrompt]

st.set_page_config(layout="wide")
st.title("NLP Chatbot")

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
            font-weight: bold;
        }

        .stSelectbox > label > div > p{
            font-size: 1.5em;
            font-weight: bold;
        }
            
        .stAudioInput > label > div > P{
            font-size: 1.5em;
            font-weight: bold;
        }

        .stButton > button{
            width: 100%;
        }

    </style>
    
    """
st.markdown(htmlStyle, unsafe_allow_html=True)

with st.sidebar:
    selectedOption = st.selectbox("Model", ["Gemini 1.5 Flash", "Gemini 1.5 Pro", "Gemini 2.0 Flash EXP", "Llama 3.3", "Mixtral"])

    st.session_state.speechEnabled = st.checkbox("Enable Speech Reply", value=False)
    st.session_state.stopWordsEnabled = st.checkbox("Enable Stop Words Removal", value=False)

    if selectedOption != st.session_state.modelName:

        st.session_state.modelName = selectedOption

        if selectedOption == "Gemini 1.5 Flash":
            st.session_state.modelName = "Gemini 1.5 Flash"
            st.session_state.model = genai.GenerativeModel("gemini-1.5-flash")

        elif selectedOption == "Gemini 1.5 Pro":
            st.session_state.modelName = "Gemini 1.5 Pro"
            st.session_state.model = genai.GenerativeModel("gemini-1.5-pro")

        elif selectedOption == "Gemini 2.0 Flash EXP":
            st.session_state.modelName = "Gemini 2.0 Flash EXP"
            st.session_state.model = genai.GenerativeModel("gemini-2.0-flash-exp")

        elif selectedOption == "Llama 3.3":
            st.session_state.modelName = "Llama 3.3"
            st.session_state.groqModel = "llama-3.3-70b-versatile"
            
        else:
            st.session_state.modelName = "Mixtral"
            st.session_state.groqModel = "mixtral-8x7b-32768"


    if st.button("Pause Reply"):
        pygame.mixer.init()
        pygame.mixer.music.pause()

    with st.form("Form1", border=False, clear_on_submit=True):
        uploadedFile = st.file_uploader("File Uploader", type=[".pdf", '.mp3', '.wav'], accept_multiple_files=False)
        submitted1 = st.form_submit_button("Submit")

    if submitted1:
        if not uploadedFile:
            st.error("No file uploaded.")

        elif uploadedFile.name.lower().endswith(".pdf"):
            pdf_reader = PdfReader(uploadedFile)
            textContent = ""

            for page in pdf_reader.pages:
                if page.extract_text() is not None:
                    textContent += page.extract_text() + "\n"

            if st.session_state.stopWordsEnabled:
                textContent = removeStopWords(textContent)

            if st.session_state.modelName not in ["Llama 3.3", "Mixtral"]:

                model = st.session_state.model 
                chat = st.session_state.chat
                response = chat.send_message("PDF Upload: Please Summarized  \n" + textContent)
                response = (st.session_state.modelName) + " :  \n" + response.text

                textToSpeech(response, st.session_state.speechEnabled)

                st.session_state.messages.append({"role": "user", "parts": "PDF Upload"})
                st.session_state.messages.append({"role": "assistant", "parts": response})
                saveChatHistory()
            
            else:
                groqChatHistory = st.session_state.groqChatHistory
                groqModel = st.session_state.groqModel

                groqChatHistory.append({"role": "user", "content": "PDF Upload: Please Summarized  \n" + textContent})

                response = client.chat.completions.create(model=groqModel, messages=groqChatHistory, max_tokens=32768, temperature=1.0)
                response = (st.session_state.modelName) + " :  \n" + response.choices[0].message.content
                textToSpeech(response, st.session_state.speechEnabled)

                st.session_state.groqChatHistory.append({
                    "role": "assistant",
                    "content": response
                })

                st.session_state.messages.append({"role": "user", "parts": "PDF Upload"})
                st.session_state.messages.append({"role": "assistant", "parts": response})
                saveChatHistory()
                        
        else:
            if uploadedFile.name.lower().endswith(".mp3"):
                mimeType = "audio/mpeg"
            else:
                mimeType = "audio/wav"
            
            if st.session_state.modelName not in ["Llama 3.3", "Mixtral"]:

                model = st.session_state.model 
                chat = st.session_state.chat
                audioFile = genai.upload_file(uploadedFile, mime_type=mimeType)
                response = chat.send_message([audioFile, "Describe it"])
                response = (st.session_state.modelName) + " :  \n" + response.text
                textToSpeech(response, st.session_state.speechEnabled)

                st.session_state.messages.append({"role": "user", "parts": "Audio Upload"})
                st.session_state.messages.append({"role": "assistant", "parts": response})
                saveChatHistory()

            else:

                if uploadedFile.name.lower().endswith(".wav"):
                    
                    with sr.AudioFile(uploadedFile) as source:
                        audio = recognizer.record(source)

                    try:
                        text = recognizer.recognize_google(audio) 
                    except sr.UnknownValueError:
                        text = "Could not understand the audio"
                    except sr.RequestError as e:
                        text = "API request failed, please try again later"

                    if st.session_state.stopWordsEnabled:
                        text = removeStopWords(text)

                    groqChatHistory = st.session_state.groqChatHistory
                    groqModel = st.session_state.groqModel

                    groqChatHistory.append({"role": "user", "content": "Audio Upload: Please describe it.  \n" + text})

                    response = client.chat.completions.create(model=groqModel, messages=groqChatHistory, max_tokens=32768, temperature=1.0)
                    response = (st.session_state.modelName) + " :  \n" + response.choices[0].message.content
                    textToSpeech(response, st.session_state.speechEnabled)

                    st.session_state.groqChatHistory.append({
                        "role": "assistant",
                        "content": response
                    })

                    st.session_state.messages.append({"role": "user", "parts": "Audio Upload"})
                    st.session_state.messages.append({"role": "assistant", "parts": response})
                    saveChatHistory()

                else:
                    st.error("This model does not support mp3 format.")


    with st.form("Form2", clear_on_submit=True):

        audioInput = st.audio_input("Audio Input")
        submitted2 = st.form_submit_button("Submit")
            
        if submitted2:

            if not audioInput:
                st.error("No audio.")

            else:
                with st.spinner("Processing audio..."):

                    if st.session_state.modelName not in ["Llama 3.3", "Mixtral"]:

                        model = st.session_state.model 
                        chat = st.session_state.chat
                        audio = genai.upload_file(audioInput, mime_type="audio/wav")
                        response = chat.send_message([audio, "Describe this audio clip"])
                        response = (st.session_state.modelName) + " :  \n" + response.text
                        textToSpeech(response, st.session_state.speechEnabled)

                        st.session_state.messages.append({"role": "user", "parts": "Audio Upload"})
                        st.session_state.messages.append({"role": "assistant", "parts": response})
                    
                        saveChatHistory()

                    else:
                        with sr.AudioFile(audioInput) as source:
                            audio = recognizer.record(source)

                        try:
                            text = recognizer.recognize_google(audio) 
                        except sr.UnknownValueError:
                            text = "Could not understand the audio"
                        except sr.RequestError as e:
                            text = "API request failed, please try again later"

                        if st.session_state.stopWordsEnabled:
                                text = removeStopWords(text)

                        groqChatHistory = st.session_state.groqChatHistory
                        groqModel = st.session_state.groqModel

                        groqChatHistory.append({"role": "user", "content": "Audio Upload: Please describe or transcribe it.  \n" + text})

                        response = client.chat.completions.create(model=groqModel, messages=groqChatHistory, max_tokens=32768, temperature=1.0)
                        response = (st.session_state.modelName) + " :  \n" + response.choices[0].message.content
                        textToSpeech(response, st.session_state.speechEnabled)

                        st.session_state.groqChatHistory.append({
                            "role": "assistant",
                            "content": response
                        })

                        st.session_state.messages.append({"role": "user", "parts": "Audio Upload"})
                        st.session_state.messages.append({"role": "assistant", "parts": response})

                        saveChatHistory()


    if st.button("Clear Chat"):
        
        os.remove("chatHistory")

        st.session_state.messages = [
            {"role": "user", "parts": "Hello"},
            {"role": "assistant", "parts": "Gemini 1.5 Flash: Great to meet you. What would you like to know?"}
        ]

        saveChatHistory()
        st.success("Chat history cleared")


       
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["parts"])

if userInput:=st.chat_input("Message Chatbot"): 

    with st.chat_message("user"):
        st.markdown(userInput)

    if st.session_state.stopWordsEnabled:
        userInput = removeStopWords(userInput)

    if st.session_state.modelName not in ["Llama 3.3", "Mixtral"]:

        model = st.session_state.model 
        chat = st.session_state.chat    
        response = chat.send_message(userInput)
        response = (st.session_state.modelName) + "  \n" + response.text    
        textToSpeech(response, st.session_state.speechEnabled)

        with st.chat_message("assistant"):
            st.markdown(response)   

        st.session_state.messages.append({"role": "user", "parts": userInput})
        st.session_state.messages.append({"role": "assistant", "parts": response})

    else:

        groqChatHistory = st.session_state.groqChatHistory
        groqModel = st.session_state.groqModel

        groqChatHistory.append({"role": "user", "content": userInput})

        responseRaw = client.chat.completions.create(model=groqModel, messages=groqChatHistory, max_tokens=32768, temperature=1.0).choices[0].message.content
        response = f"{st.session_state.modelName} :  \n{responseRaw}"
        textToSpeech(response, st.session_state.speechEnabled)

        with st.chat_message("assistant"):
            st.markdown(response)   

        st.session_state.groqChatHistory.append({
            "role": "assistant",
            "content": responseRaw
        })

        st.session_state.messages.append({"role": "user", "parts": userInput})
        st.session_state.messages.append({"role": "assistant", "parts": response})


    saveChatHistory()
    
