import streamlit as st

if st.session_state.user_token is None:
    st.info('Please Login from the Home page and try again.')
    st.stop()
import requests

st.write("Declare Intent")

if st.session_state.user_token is not None:
    if intent := st.chat_input("Declare your intent.."):
        st.chat_message("user").markdown(intent)

        with st.chat_message("assistant"):
            headers = {'Authorization': f'Bearer {st.session_state.user_token}'}
            data = {'method': 'user', 'token': st.session_state.user_token, 'intent': intent}
            response = requests.post("http://127.0.0.1:5000/declare-intent", headers=headers, json=data)
            st.write(response.json())
