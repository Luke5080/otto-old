from typing import Union

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from matplotlib.figure import Figure

from otto.gui.api_handler import ApiHandler

st.set_page_config(
    page_title="Otto"
)

# will be cached until session state is cleared
st_api_handler = ApiHandler.get_api_handler()


def create_latest_data_df() -> Union[pd.DataFrame, None]:
    """
    Function to create a Pandas dataframe for data retrieved in /latest-activity API call.
    If no data is found, the function will return None
    """
    latest_data_df = None

    latest_data = st_api_handler.get_latest_activity()

    if latest_data:
        latest_data_df = pd.DataFrame.from_dict(latest_data, orient='index')
        latest_data_df.reset_index(inplace=True)
        latest_data_df.rename(
            columns={'index': 'Timestamp', 'declaredBy': 'Declared By', 'intent': 'Intent', 'outcome': 'Outcome'},
            inplace=True)

    return latest_data_df


def create_weekly_data_df() -> Union[pd.DataFrame, None]:
    """
    Function to create a Pandas dataframe for data retrieved in /weekly-activity API call.
    If no data is found, the function will return None
    """
    weekly_data_df = None

    weekly_data = st_api_handler.get_weekly_activity()

    if weekly_data:
        weekly_data_df = pd.DataFrame(list(weekly_data.items()), columns=["date_of_week", "intents"])

        weekly_data_df["date_of_week"] = pd.to_datetime(weekly_data_df["date_of_week"])

        weekly_data_df = weekly_data_df.sort_values(by="date_of_week")

        weekly_data_df.set_index("date_of_week", inplace=True)

        full_date_range = pd.date_range(start=weekly_data_df.index.min(), end=weekly_data_df.index.max())
        weekly_data_df = weekly_data_df.reindex(full_date_range)

        weekly_data_df["intents"] = weekly_data_df["intents"].interpolate()

    return weekly_data_df


def create_top_activity_df() -> Union[pd.DataFrame, None]:
    """
    Function to create a Pandas dataframe for data retrieved in /top-activity API call.
    If no data is found, the function will return None
    """
    top_activity_df = None
    top_activity = st_api_handler.get_top_activity()

    if top_activity:
        top_activity_df = pd.DataFrame(list(top_activity.items()), columns=["User", "Count"])
        top_activity_df = top_activity_df.sort_values(by="Count", ascending=False)

    return top_activity_df


def create_model_usage_pie_chart() -> Union[None, Figure]:
    """
    Function to create a pie chart for model_usage data retrieved from /model-usage API.
    If no data is found, the function will return None
    """
    model_data = st_api_handler.get_model_usage()

    fig = None

    if model_data is not None:
        y = []
        mylabels = []
        for model, count in model_data.items():
            y.append(count)
            mylabels.append(model)

        fig, ax = plt.subplots()
        fig.patch.set_alpha(0)
        ax.set_facecolor('none')
        ax.pie(y, shadow=True)
        legend = ax.legend(mylabels, loc="best", frameon=False)
        for text in legend.get_texts():
            text.set_color("white")

    return fig


if "user_token" not in st.session_state:
    st.session_state.user_token = None

placeholder = st.empty()

if st.session_state.user_token is None:
    with placeholder.form("login"):
        left_co, cent_co, last_co = st.columns(3)
        with cent_co:
            st.image("otto/gui/otto-banner.png")

        st.markdown("#### Enter your credentials")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        submit = st.form_submit_button("Login")

    if submit:
        authentication_response = st_api_handler.login(username, password)

        if authentication_response.status_code != 200:
            st.error(f"Login Failed: {authentication_response['message']}")
        else:
            placeholder.empty()
            st.session_state.user_token = authentication_response.json()['token']
            st_api_handler.set_token(authentication_response.json()['token'])
            st.rerun()

if st.session_state.user_token is not None:
    col = st.columns((60, 50), gap='medium')

    # create data dataframes to be visualised on dashboard
    latest_data_table = create_latest_data_df()
    weekly_data_table = create_weekly_data_df()
    top_activity_table = create_top_activity_df()

    with col[0]:
        st.subheader('Recently declared intents')

        if latest_data_table is not None:
            for index, row in latest_data_table.iterrows():
                with st.expander(f"Intent: {row['Intent']}"):
                    st.write(f"**Declared By**: {row['Declared By']}")
                    st.write(f"**Intent**: {row['Intent']}")
                    st.write(f"**Outcome**\n:")
                    for outcome in row['Outcome']:
                        st.markdown(f"- {outcome}")

        else:
            st.write("No data available")

        st.subheader('Activity in the last week')

        if weekly_data_table is not None:
            st.line_chart(weekly_data_table["intents"])
        else:
            st.write("No data available")

    with col[1]:
        st.subheader("Model Usage")

        fig = create_model_usage_pie_chart()

        if fig is not None:
            st.pyplot(fig, use_container_width=True)
        else:
            st.write("No data available")
        st.subheader("Usage by users/applications")

        if top_activity_table is not None:
            st.table(top_activity_table)

        else:
            st.write("No Data Available")
