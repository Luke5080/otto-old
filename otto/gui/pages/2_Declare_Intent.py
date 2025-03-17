import streamlit as st
if st.session_state.user_token is None:
    st.info('Please Login from the Home page and try again.')
    st.stop()
st.write("Declare Intent")
