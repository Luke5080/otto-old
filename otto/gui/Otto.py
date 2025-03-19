import matplotlib.pyplot as plt

import numpy as np
import pandas as pd
import streamlit as st
import graphviz
import requests
from langchain_core.messages import HumanMessage
import time

st.set_page_config(
   page_title="Otto"
)


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
   col = st.columns((60,50), gap='medium')

   headers = {'Authorization': f'Bearer {st.session_state.user_token}'}
   response = requests.get("http://127.0.0.1:5000/latest-activity", headers=headers)
   data = response.json()

   df = pd.DataFrame.from_dict(data['message'], orient='index')
   df.reset_index(inplace=True)
   df.rename(columns={'index': 'Timestamp', 'declaredBy': 'Declared By', 'intent': 'Intent', 'outcome': 'Outcome'}, inplace=True)

   weekly_activity = requests.get("http://127.0.0.1:5000/weekly-activity", headers=headers)

   data = weekly_activity.json()

   if "message" in data:
        weekly_data = data["message"]

        wk_df = pd.DataFrame(list(weekly_data.items()), columns=["date_of_week", "intents"])

        wk_df["date_of_week"] = pd.to_datetime(wk_df["date_of_week"])

        wk_df = wk_df.sort_values(by="date_of_week")

        wk_df.set_index("date_of_week", inplace=True)

        full_date_range = pd.date_range(start=wk_df.index.min(), end=wk_df.index.max())
        wk_df = wk_df.reindex(full_date_range)

        wk_df["intents"] = wk_df["intents"].interpolate()

   with col[0]:
      st.subheader('Recently declared intents')

      for index, row in df.iterrows():
          with st.expander(f"Intent: {row['Intent']}"):
               st.write(f"**Declared By**: {row['Declared By']}")
               st.write(f"**Intent**: {row['Intent']}")
               st.write(f"**Outcome**: {row['Outcome']}")

               graph = graphviz.Digraph()
               for i in range(0, len(row['Outcome']) - 1):
                   graph.edge(row['Outcome'][i], row['Outcome'][i+1])
               st.graphviz_chart(graph)
      st.subheader('Activity in the last week')
      st.line_chart(wk_df["intents"])

   with col[1]:
        st.subheader("Model Usage")

        y = np.array([35, 25, 25, 15])
        mylabels = ["gpt-4o", "gpt-4o-mini", "Deepseek", "gpt-o3-mini"]

        fig, ax = plt.subplots()
        fig.patch.set_alpha(0)
        ax.set_facecolor('none')
        ax.pie(y, shadow=True)
        ax.legend(mylabels, loc="best",frameon=False)
        st.pyplot(fig, use_container_width=True)
        resp = requests.get("http://127.0.0.1:5000/top-activity", headers=headers)
        data  = resp.json().get("message", {})
        st.subheader("Usage by users/applications")
        df2 = pd.DataFrame(list(data.items()), columns=["User", "Count"])
        df2 = df2.sort_values(by="Count", ascending=False)
        st.table(df2)
