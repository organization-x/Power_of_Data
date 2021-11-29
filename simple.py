from matplotlib.backends.backend_agg import RendererAgg
import streamlit as st
import numpy as np
import pandas as pd
import xmltodict
from pandas import json_normalize
import urllib.request
import seaborn as sns
import matplotlib
from matplotlib.figure import Figure
from PIL import Image
import gender_guesser.detector as gender
from streamlit_lottie import st_lottie
import requests
import glob
import os
import matplotlib.pyplot as plt

# this function imports all csv's from the data_directory into their own correctly named pandas dataframes
def import_data_into_dataframes(data_directory):
    file_list = glob.glob(data_directory + "/*.csv")
    # print(file_list)
    df_list = []
    for file in file_list:
        df_list.append(pd.read_csv(file))
    return df_list


# this function gets all columns from each dataframe and prints them with a blank line between each
def print_all_columns(df_list):
    for df in df_list:
        print(df.columns)
        print()


# this function merges both dataframes into one dataframe using the 'name' column as the key
def merge_dataframes(df_list):
    df = pd.merge(df_list[0], df_list[1], on="name")
    # drop rows that have empty columns and duplicates
    df = df.dropna(axis=0, how="any")
    df = df.drop_duplicates(subset=["name"], keep="first")
    # drop the columns: 'state_code', 'state','degree_length','rank'
    df = df.drop(columns=["state_code", "state", "degree_length", "rank"])
    return df


# state statistics, return a styled display of the dataframe and the dataframe
def make_state_stats(df):
    # get all states
    states = df.state_name.unique()

    # make state_stats dataframe, index = states, columns = ['number of schools','average early_career_pay','average mid_career_pay','average make_world_better_percent', 'average stem_percent','average room_and_board',  'average in_state_tuition', 'average in_state_total',	'average out_of_state_tuition'	'average out_of_state_total']
    state_stats = pd.DataFrame(
        index=states,
        columns=[
            "number of schools",
            "average early_career_pay",
            "average mid_career_pay",
            "average make_world_better_percent",
            "average stem_percent",
            "average room_and_board",
            "average in_state_tuition",
            "average in_state_total",
            "average out_of_state_tuition",
            "average out_of_state_total",
        ],
    )
    state_stats = state_stats.apply(pd.to_numeric)
    # fill each of the state_stats columns using data from df
    for state in states:
        state_stats.loc[state, "number of schools"] = len(df[df.state_name == state])
        state_stats.loc[state, "average early_career_pay"] = df[df.state_name == state][
            "early_career_pay"
        ].mean()
        state_stats.loc[state, "average mid_career_pay"] = df[df.state_name == state][
            "mid_career_pay"
        ].mean()
        state_stats.loc[state, "average make_world_better_percent"] = df[
            df.state_name == state
        ]["make_world_better_percent"].mean()
        state_stats.loc[state, "average stem_percent"] = df[df.state_name == state][
            "stem_percent"
        ].mean()
        state_stats.loc[state, "average room_and_board"] = df[df.state_name == state][
            "room_and_board"
        ].mean()
        state_stats.loc[state, "average in_state_tuition"] = df[df.state_name == state][
            "in_state_tuition"
        ].mean()
        state_stats.loc[state, "average in_state_total"] = df[df.state_name == state][
            "in_state_total"
        ].mean()
        state_stats.loc[state, "average out_of_state_tuition"] = df[
            df.state_name == state
        ]["out_of_state_tuition"].mean()
        state_stats.loc[state, "average out_of_state_total"] = df[
            df.state_name == state
        ]["out_of_state_total"].mean()
    
    # convert all columns to numeric
    state_stats = state_stats.apply(pd.to_numeric)
    # make columns for four year average out of state and in state total
    state_stats['four year average out of state total'] = state_stats['average out_of_state_total'] * 4
    state_stats['four year average in state total'] = state_stats['average in_state_total'] * 4
    # make column calculating how many years on average to repay four year average in and our of state based on average early career pay in index 0
    state_stats['years to repay in state 4 year uni based on early career pay'] =  state_stats['four year average in state total'] / state_stats['average early_career_pay']
    state_stats['years to repay out of state 4 year uni based on early career pay'] = state_stats['four year average out of state total'] / state_stats['average early_career_pay'] 
    # make column calculating how many years on average to repay four year average in and our of state based on average mid career pay in index 0
    state_stats['years to repay in state 4 year uni based on mid career pay'] =  state_stats['four year average in state total'] / state_stats['average mid_career_pay']
    state_stats['years to repay out of state 4 year uni based on mid career pay'] = state_stats['four year average out of state total'] / state_stats['average mid_career_pay'] 
    # move 'years to repay out of state 4 year uni based on early career pay' to the front of the dataframe
    state_stats = state_stats.reindex(columns=['years to repay in state 4 year uni based on early career pay', 'years to repay out of state 4 year uni based on early career pay',
    'years to repay in state 4 year uni based on mid career pay', 'years to repay out of state 4 year uni based on mid career pay',
    'number of schools', 'average early_career_pay', 'average mid_career_pay', 'average make_world_better_percent', 'average stem_percent',
    'average room_and_board',  'average in_state_tuition', 'average in_state_total',	'average out_of_state_tuition',
    'average out_of_state_total', 'four year average out of state total', 'four year average in state total'])

    styled = (
        state_stats.style.apply(highlight_above_avg)
        .apply(highlight_top)
        .apply(highlight_below_avg)
    )

    return styled, state_stats


def highlight_above_avg(s):
    s_avg = s >= s.quantile(0.50)
    return ["background: lightgreen" if cell else "" for cell in s_avg]


def highlight_below_avg(s):
    s_avg = s < s.quantile(0.10)
    return ["background: red" if cell else "" for cell in s_avg]


def highlight_top(s):
    s_avg = s > s.quantile(0.90)
    return ["color: blue" if cell else "" for cell in s_avg]


# plot the relationship between 'average stem_percent' and 'average early_career_pay'
# use seaborn to plot a scatter plot of the data
def plot_stem_early_career(df):
    fig = Figure()
    ax = fig.subplots()
    # create a scatter plot of 'average stem_percent' vs 'average early_career_pay'
    sns.scatterplot(
        x="average stem_percent", y="average early_career_pay", data=df, ax=ax
    )
    # add a title
    ax.set_title("Average STEM Percent vs Average Early Career Pay")
    # add a label to the y-axis
    ax.set_ylabel("Average Early Career Pay")
    # add a label to the x-axis
    ax.set_xlabel("Average STEM Percent")
    # add label with the index to each point at a 15 degree angle
    for i, txt in enumerate(df.index):
        ax.annotate(
            txt,
            (df["average stem_percent"][i], df["average early_career_pay"][i]),
            rotation=15,
        )
    # show the plot
    return fig


# plot similar to plot_stem_early_career but for 'four year average in state total' and 'average early_career_pay'
def plot_4instate_early_career(df):
    fig = Figure()
    ax = fig.subplots()
    sns.scatterplot(
        x="four year average in state total",
        y="average early_career_pay",
        data=df,
        ax=ax,
    )
    ax.set_title("Average In State Tuition vs Average Early Career Pay")
    ax.set_ylabel("Average Early Career Pay")
    ax.set_xlabel("Average In State Tuition")
    for i, txt in enumerate(df.index):
        ax.annotate(
            txt,
            (
                df["four year average in state total"][i],
                df["average early_career_pay"][i],
            ),
            rotation=15,
        )
    return fig


# create a streamlit dashboard that:
# 1. Shows the styled dataframe outputted as styled by the state_stats function
# 2. Shows a scatter plot of the data created with plot_stem_early_career
# 3. Shows a scatter plot of the data created with plot_4instate_early_career

directory = os.getcwd() + "/Data/"
df_list = import_data_into_dataframes(directory)
df = merge_dataframes(df_list)
styled, state_stats = make_state_stats(df)

matplotlib.use("agg")

_lock = RendererAgg.lock


sns.set_style("darkgrid")
row0_spacer1, row0_1, row0_spacer2, row0_2, row0_spacer3 = st.columns(
    (0.1, 2, 0.2, 1, 0.1)
)

row0_1.title("Analyzing College Tuition and Paying it Off")


with row0_2:
    st.write("")

row0_2.subheader("A Streamlit web app by [Ai-Camp](http://www.ai-camp.org)")

row1_spacer1, row1_1, row1_spacer2 = st.columns((0.1, 3.2, 0.1))

with row1_1:
    st.markdown(
        "Hey there! Here's where you can give a warm welcome to your viewer and give context to your data coming!"
    )

row2_spacer1, row2_1, row2_spacer2 = st.columns((0.1, 3.2, 0.1))

# show the styled dataframe in row2_2
with row2_1, _lock:
    st.write(styled)

row3_space1, row3_1, row3_space2, row3_2, row3_space3 = st.columns(
    (0.1, 1, 0.1, 1, 0.1)
)

with row3_1, _lock:
    st.subheader("Scatter Plot of STEM vs Early Career Pay")
    st.pyplot(plot_stem_early_career(state_stats))

with row3_2, _lock:
    st.subheader("Scatter Plot of In State Tuition vs Early Career Pay")
    st.pyplot(plot_4instate_early_career(state_stats))
