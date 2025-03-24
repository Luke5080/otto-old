import time

import streamlit as st

from otto.gui.api_handler import ApiHandler


def generate_output(complete_output: str):
    """ Generate output in a ChatGPT style stream where each word
    is yielded with a pause of 0.02 seconds """
    for word in complete_output.split(" "):
        yield word + " "
        time.sleep(0.02)


if st.session_state.user_token is None:
    st.info('Please Login from the Home page and try again.')
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.user_token is not None:
    st.header("Declare Intent")

    st_api_handler = ApiHandler()
    st_api_handler.set_token(st.session_state.user_token)

    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])

    if intent := st.chat_input("Declare your intent.."):
        st.chat_message("user").markdown(intent)
        st.session_state.messages.append({"role": "user", "content": intent})

        with st.chat_message("assistant"):
            with st.spinner("Contacting IntentProcessor.."):
                intent_processor_response = st_api_handler.declare_intent(intent)

            output_response = st.write_stream(generate_output(intent_processor_response.get("message", "")))

            with st.expander("Operations completed:"):
                st.write(intent_processor_response.get("operations", ""))

            st.session_state.messages.append({'role': 'assistant', 'content': output_response})
