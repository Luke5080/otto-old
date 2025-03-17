import streamlit as st
import requests
from langchain_core.messages import HumanMessage
import time

st.set_page_config(
   page_title="Otto"
)


# Initialize session state for user token
if "user_token" not in st.session_state:
    st.session_state.user_token = None

placeholder = st.empty()

if st.session_state.user_token is None:
    with placeholder.form("login"):
        st.markdown("#### Enter your credentials")
        username = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    headers = {'Content-Type': 'application/json'}
    data = {'method': 'user', 'username': username, 'password': password}

    if submit:
        authentication_response = requests.post("http://127.0.0.1:5000/login", headers=headers, json=data)

        if authentication_response.status_code != 200:
            st.error(f"Login Failed: {authentication_response.json()['message']}")
        else:
            placeholder.empty()
            st.session_state.user_token = authentication_response.json()['token']
            st.rerun()

if st.session_state.user_token is not None:
    if intent := st.chat_input("Declare your intent.."):
        st.chat_message("user").markdown(intent)

        with st.chat_message("assistant"):            
            headers = {'Authorization': f'Bearer {st.session_state.user_token}'}
            data = {'method': 'user', 'token': st.session_state.user_token, 'intent': intent}
            response = requests.post("http://127.0.0.1:5000/declare-intent", headers=headers, json=data)
            st.write(response.json())




