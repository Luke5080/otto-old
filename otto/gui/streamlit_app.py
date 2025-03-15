import streamlit as st
import requests

st.title("Input your Query")
selector = st.text_area(label="Input Query", value="", height=None, max_chars=None, key=None, help=None, on_change=None,
                        args=None, kwargs=None, placeholder=None, disabled=False, label_visibility="hidden")
query_text_sql = selector

if st.button("Search", type='primary'):
    lol = {'name': query_text_sql}
    data = requests.post("http://localhost:5000/test", headers={'Content-Type':'application/json'}, json=lol).json()
    output_query = data["message"]
    st.header("Query Response")
    st.write(output_query)
