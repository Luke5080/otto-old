import time

import requests
import streamlit as st


def generate_output(complete_output: str):
    for word in complete_output.split(" "):
        yield word + " "
        time.sleep(0.02)


if st.session_state.user_token is None:
    st.info('Please Login from the Home page and try again.')
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.header("Declare Intent")
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if st.session_state.user_token is not None:
    if intent := st.chat_input("Declare your intent.."):
        st.chat_message("user").markdown(intent)
        st.session_state.messages.append({"role": "user", "content": intent})

        with st.chat_message("assistant"):
            headers = {'Authorization': f'Bearer {st.session_state.user_token}'}
            data = {'method': 'user', 'token': st.session_state.user_token, 'intent': intent,
                    'stream_type': 'AgentMessages'}

            with st.spinner("Contacting IntentProcessor.."):
                response = requests.post("http://127.0.0.1:5000/declare-intent", headers=headers, json=data)

            output_response = st.write_stream(generate_output(response.json()['message']))
            st.session_state.messages.append({'role': 'assistant', 'content': output_response})
