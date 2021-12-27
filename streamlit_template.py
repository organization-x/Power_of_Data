# IMPORT ALL NECESSARY PACKAGES HERE
####################################
import streamlit as st
st.set_page_config(layout="wide") # this makes the streamlit use the full width of the page
import pandas as pd
import numpy as np
import plotly.express as px
####################################

# ADD ALL FUNCTIONS FROM YOUR JUPYTER NOTEBOOKS HERE ONCE TESTED
# EACH FUNCTION MUST BE SELF CONTAINED, TO TEST THAT THEY ARE RUN THEM IN A JUPYTER NOTEBOOK FOR TESTING (see function_testing_notebook)
######################################################################
######################################################################
# this function returns our two dataframes we need for everything else
def load_my_data():
    salary_potential = pd.read_csv("./Data/salary_potential.csv")
    tuition = pd.read_csv("./Data/tuition_cost.csv")
    return salary_potential, tuition

# this function fills the state based on state_code for non-states
def fill_state(row):
    if row['state_code'] == 'AS':
        return 'American Samoa'
    elif row['state_code'] == 'DC':
        return 'District of Columbia'
    elif row['state_code'] == 'PR':
        return 'Puerto Rico'
    elif row['state_code'] == 'GU':
        return 'Guam'
    elif row['state_code'] == 'VI':
        return 'Virgin Islands'
    else:
        return row['state']

# this function cleans and merges our two dataframes, returns one merged_df
def clean_and_merge_dfs(tuition, salary_potential):
    # drop room and board (axis = 1 --> column)
    tuition = tuition.drop('room_and_board', axis=1)
    # drop rows with empty make world better place (axis = 0 --> row)
    salary_potential = salary_potential.dropna(subset=['make_world_better_percent'])
    # inplace = True means that we want the rename to occur in existing dataframe, not return a new one
    # this is an example of how to rename a column if you need to
    #salary_potential.rename({'state_name': 'state'}, axis=1, inplace=True)
    # we create a new dataframe called merged_df that is the combined one
    merged_df = pd.merge(tuition, salary_potential, on='name')
    # replace mismatched rows
    to_replace = ['New-York', 'North-Carolina', 'South-Dakota', 'South-Carolina',
       'New-Jersey', 'West-Virginia', 'Rhode-Island', 'New-Hampshire',
       'North-Dakota', 'New-Mexico']
    replace_with = ['New York', 'North Carolina', 'South Dakota', 'South Carolina',
           'New Jersey', 'West Virginia', 'Rhode Island', 'New Hampshire',
           'North Dakota', 'New Mexico']
    for i in range(len(to_replace)):
        merged_df["state_name"].replace({to_replace[i]: replace_with[i]}, inplace=True)
    # drop the duplicative (and slightly incorrect) column 'state'
    merged_df.drop(['state','state_code'], axis=1, inplace=True)
    # return the merged dataframe
    return merged_df

# Return a state_stats df that averages the statistics we are curious about
def state_stats_df(merged_df):
    # get a list of all state_name's
    states = merged_df.state_name.unique()

    # Create a column in a new dataframe for each stat I want
    state_stats = pd.DataFrame(index=states, columns=['number of schools','average early_career_pay',
                                                      'average mid_career_pay','average make_world_better_percent',
                                                      'average stem_percent','average in_state_tuition', 
                                                      'average out_of_state_tuition'])
    # Fill in the columns for each state
    for state in states:
        state_stats.loc[state, 'number of schools'] = len(merged_df[merged_df.state_name == state])
        state_stats.loc[state, 'average early_career_pay'] = merged_df[merged_df.state_name == state]['early_career_pay'].mean()
        state_stats.loc[state, 'average mid_career_pay'] = merged_df[merged_df.state_name == state]['mid_career_pay'].mean()
        state_stats.loc[state, 'average make_world_better_percent'] = merged_df[merged_df.state_name == state]['make_world_better_percent'].mean()
        state_stats.loc[state, 'average stem_percent'] = merged_df[merged_df.state_name == state]['stem_percent'].mean()
        state_stats.loc[state, 'average in_state_tuition'] = merged_df[merged_df.state_name == state]['in_state_tuition'].mean()
        state_stats.loc[state, 'average out_of_state_tuition'] = merged_df[merged_df.state_name == state]['out_of_state_tuition'].mean()
    # sort alphabetically by state
    state_stats.sort_index(inplace = True)
    return state_stats

# Highlighting functions for our dataframe
def highlight_above_avg(state):
    # state_TF will check every row (state) and give a True/False value depending on the condition asked
    # e.g. if the value is >.50 quantile (average value) for the column
    state_TF = state >= state.quantile(.50)
    return ['background: lightgreen' if state else '' for state in state_TF]
def highlight_below_avg(state):
    state_TF = state < state.quantile(.10)
    return ['background: red' if state else '' for state in state_TF]
def highlight_top(s):   
    state_TF = s > s.quantile(0.90)
    return ['color: blue' if state else '' for state in state_TF]
# This function puts them all together
def return_highlighted_df(state_stats):
    return state_stats.style.apply(highlight_above_avg).apply(highlight_below_avg).apply(highlight_top)

def add_details(state_stats):
    # convert all columns to numeric
    state_stats = state_stats.apply(pd.to_numeric)
    # make columns for four year average out of state and in state total
    state_stats['four year average out of state tuition'] = state_stats['average out_of_state_tuition'] * 4
    state_stats['four year average in state tuition'] = state_stats['average in_state_tuition'] * 4
    # make column calculating how many years on average to repay four year average in and our of state based on average early career pay in index 0
    state_stats['years to repay in state 4 year uni based on early career pay'] =  state_stats['four year average in state tuition'] / state_stats['average early_career_pay']
    state_stats['years to repay out of state 4 year uni based on early career pay'] = state_stats['four year average out of state tuition'] / state_stats['average early_career_pay'] 
    # make column calculating how many years on average to repay four year average in and our of state based on average mid career pay in index 0
    state_stats['years to repay in state 4 year uni based on mid career pay'] =  state_stats['four year average in state tuition'] / state_stats['average mid_career_pay']
    state_stats['years to repay out of state 4 year uni based on mid career pay'] = state_stats['four year average out of state tuition'] / state_stats['average mid_career_pay'] 
    # move 'years to repay out of state 4 year uni based on early career pay' to the front of the dataframe
    state_stats = state_stats.reindex(columns=['four year average in state tuition', 'four year average out of state tuition', 'years to repay in state 4 year uni based on early career pay', 'years to repay out of state 4 year uni based on early career pay',
    'years to repay in state 4 year uni based on mid career pay', 'years to repay out of state 4 year uni based on mid career pay',
    'number of schools', 'average early_career_pay', 'average mid_career_pay', 'average make_world_better_percent', 'average stem_percent',
    'average in_state_tuition','average out_of_state_tuition'])
    return state_stats

# Define a function to add these last extras that need to be applied after our numerical calculations (highlighting for example)
def add_extras(state_stats,tuition):
    # turn the index into a column
    state_stats_extras = state_stats.reset_index(level=0)
    # rename index to state
    state_stats_extras.rename({'index': 'state'}, axis=1, inplace=True)
    # add the state_code column
    state_stats_extras = state_stats_extras.merge(tuition[['state','state_code']], on='state').drop_duplicates().reset_index(drop=True)
    return state_stats_extras

# This function returns the dataframes we need for all our visuals
# 1. state_stats, 2. state_stats_extras
def master_function_tuition():
    salary_potential,tuition=load_my_data()
    tuition['state'] = tuition.apply(lambda row : fill_state(row), axis=1)
    merged_df = clean_and_merge_dfs(tuition, salary_potential)
    state_stats = state_stats_df(merged_df)
    state_stats = add_details(state_stats)
    state_stats_extras = add_extras(state_stats,tuition)
    return state_stats, state_stats_extras
######################################################################
######################################################################


# NOW ALL WE NEED TO FOCUS ON IS DESIGNING OUR STREAMLIT PAGE WITH OUR VISUALS 
######################################################################
######################################################################
######################################################################

# BEFORE DOING ANYTHING, LETS IMPORT OUR DATA USING THE MASTER FUNCTION SO IT CAN BE USED LATER
state_stats, state_stats_extras = master_function_tuition()

# ADD A TITLE AND SUBTITLE AT THE TOP
st.title("Are There Associations With University Tuition & Professional Pay on a State-by-State Basis?")
st.subheader("BY: AI-Camp")

# THIS SECTION SHOWS HOW YOU CAN HAVE TWO COLUMNS SIDE BY SIDE, THE RATIO DEFINES HOW MUCH SPACE EACH COLUMN TAKES UP
# IN THIS CASE 3,2 MEANS row0_1 WILL BE 3X WIDE AND row0_2 WILL BE 2X WIDE
# YOU WILL LIKELY HAVE TO MANUALLY SET THE WIDTH AND HEIGHT OF VISUALS
row0_1, row0_2 = st.columns((3,2))
with row0_1:
    st.write(return_highlighted_df(state_stats))
with row0_2:
    st.write("Having text on one side of an image makes it really nice to be able to add descriptions to a visual / dataframe.")



# THIS SECTION SHOWS HOW YOU CAN HAVE ADD A FULL WIDTH VISUAL
fig1 = px.scatter(state_stats_extras, x='four year average in state tuition', y='average mid_career_pay',
                 color='state',size='average make_world_better_percent',
                 trendline="ols", trendline_scope = 'overall',
                 title= 'Average In State Tuition vs Average % of Students Graduating with STEM Degrees')
st.plotly_chart(fig1)

# THIS SECTION SHOWS HOW YOU CAN HAVE TWO VISUALS SIDE BY SIDE, THE RATIO DEFINES HOW MUCH SPACE EACH COLUMN TAKES UP
# IN THIS CASE 2,2 MEANS row1_1 AND row1_2 WILL BE THE SAME WIDTH
# HERE WE SHOW HOW TO SET WIDTH AND HEIGHT OF VISUALS, YOU WILL HAVE TO TEST WHAT WORKS FOR YOU
row1_1, row1_2 = st.columns((1,1))
fig2 = px.choropleth(state_stats_extras, locations='state_code', locationmode="USA-states", color="four year average in state tuition", scope="usa",width=500, height=400)
fig3 = px.choropleth(state_stats_extras, locations='state_code', locationmode="USA-states", color="average early_career_pay", scope="usa",width=500, height=400)

with row1_1:
    st.write('You can add text above charts here too')
    st.plotly_chart(fig2)
with row1_2:
    st.write('Or here')
    st.plotly_chart(fig3)