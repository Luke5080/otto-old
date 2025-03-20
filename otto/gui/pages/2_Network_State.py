import streamlit as st

st.write("Network State")

import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.title("WebSocket Communication with Flask")

websocket_script = """
<script>
    var socket = io("http://127.0.0.1:6000");  

    function sendMessage() {
        var message = document.getElementById("userMessage").value;
        socket.emit('send_message', message);
    }

    socket.on('response', function(msg) {
        document.dispatchEvent(new CustomEvent("streamlit_event", {detail: msg.data}));
    });
</script>
"""

st.markdown(websocket_script, unsafe_allow_html=True)

user_message = st.text_input("Enter a message", key="userMessage")
if st.button("Send Message"):
    streamlit_js_eval(js_expressions="sendMessage()")

response = streamlit_js_eval(js_expressions="document.addEventListener('streamlit_event', (e) => e.detail)")
if response:
    st.write(f"Server: {response}")
