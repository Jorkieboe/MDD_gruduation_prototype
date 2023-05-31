import numpy as np
import pandas as pd
import streamlit as st
import requests
from math import floor
from math import ceil
import json

if 'init' not in st.session_state:
    st.session_state['init'] = True

if 'df' not in st.session_state:
    st.session_state['df'] = 1

# get challenges 
df_challenges = pd.read_csv('Challenge_template.csv', delimiter=';')
df_challenges['playerType'] = df_challenges['playerType'].str.split(',')
df_challenges = df_challenges.explode('playerType').reset_index()
df_challenges = pd.get_dummies(df_challenges, columns=['playerType']).reset_index(drop=True)
df_challenges = df_challenges.groupby(['index', 'challengesTemplate', 'distance', 'time', 'segment', 'reward']).agg({'playerType_Achiever' : 'sum', 'playerType_Socializer': 'sum','playerType_Philanthropist': 'sum', 'playerType_Free_Spirit': 'sum', 'playerType_Player': 'sum'})
df_challenges = df_challenges.reset_index()

if st.session_state['init'] == True:
    df = pd.DataFrame([], columns=df_challenges.columns)
    st.session_state['init'] = False
else:
    df = st.session_state['df']

# recommend a player type with a epsilon greedy algorithm
def epsilon_greedy_policy(df, epsilon=0.10):
    types = ['playerType_Achiever', 'playerType_Socializer','playerType_Philanthropist', 'playerType_Free_Spirit', 'playerType_Player']
    values = [df['playerType_Achiever'].count(), df['playerType_Socializer'].count(),df['playerType_Philanthropist'].count(), df['playerType_Free_Spirit'].count(), df['playerType_Player'].count()]
    df2 = pd.DataFrame(values, index=types, columns=['count']).reset_index()
    df2['count'] += 1
    # draw a 0 or 1 from a binomial distribution, where epsilon % chance to pick one.
    explore = np.random.binomial(1, epsilon)
    # if explore: choose randomly three different player types
    if explore == 1 or df2['count'].sum() < 6:
        method = 'explore'
        recs = df2.sample(n = 3)
    # if exploit: pick the top ranked player types
    else:
        method = 'exploit'
        # duplicated every player type by amount of reward
        scores_dupl = df2.loc[df2.index.repeat(df2['count'])].reset_index(drop=True)
        
        # sort values and only keep the top 75%
        scores = scores_dupl.sort_values('count', ascending=False).reset_index(drop=True)
        slice_lenght = floor(len(scores) * 0.75)
        scores = scores.loc[0: slice_lenght]

        #select three recommendations
        if len(scores) > 1:
            recs = scores.sample(n = 3)
        else:
            recs = scores.loc[0: 2]
    return recs, method

recs, method = epsilon_greedy_policy(df)
recs['index'] = recs['index'].astype('string')

def getChallenges():
    first = True
    for index, type in recs.iterrows():
        second = True
        for index2, challenge in df_challenges.iterrows():
            if challenge[type['index']] == 1:
                if(second == False):
                    challengeDF = challenge.to_frame().T
                    challengesPerType = pd.concat([challengesPerType, challengeDF], ignore_index=True)
                else:
                    challengesPerType = challenge.to_frame().T
                    second = False
        sample = challengesPerType.sample(n=1)
        if first == False:
            sampleDF = sample
            recommendedChallenges = pd.concat([recommendedChallenges, sampleDF])
        else:
            recommendedChallenges = sample
            first= False
    return recommendedChallenges

RecChallenges = getChallenges()
RecChallenges = RecChallenges.reset_index(drop=True)


def changeChallengeParameters():
    for index, challenge in RecChallenges.iterrows():
        if '<segment>' in challenge['challengesTemplate']:
            # location = [51.575283, 4.737244, 51.600514, 4.812119]
            # BaseUrl = 'https://www.strava.com/api/v3/segments/explore?'
            # response = requests.get(BaseUrl, params={'bounds': ','.join(str(b) for b in location), 'activity_type': 'running'}, headers={'Authorization': 'Bearer 844e0605ec502d933c57550480ee63630c2d83e7'})
            # data = response.json() 
            with open('segments.json', 'r') as openfile:
                data = json.load(openfile)
            segmentName = ''
            segmentDistance = 0
            for segment in data:
                newSegment = True
                for pastsegments in df['segment']:
                    if segment['name'] == pastsegments:
                        newSegment = False
                    else:
                        segmentName = segment['name']
                        segmentDistance = segment['distance']
                if newSegment == True:
                    break
            challenge['segment'] = segmentName
            challenge['distance'] = segmentDistance
        if '<distance>' in challenge['challengesTemplate']:
            pastdistances = []
            for pastdistance in df['distance']:
                pastdistances.append(pastdistance)
            if len(pastdistances) > 0:
                avg_distance = sum(pastdistances) / len(pastdistances)
                increase_percentage = 0.05  
                increase_distance = avg_distance * increase_percentage
                new_distance = avg_distance + increase_distance
                challenge['distance'] = new_distance
        if '<time>' in challenge['challengesTemplate']:
            pasttimeList = []
            for pasttime in df['distance']:
                pasttimeList.append(pasttime)
            if len(pasttimeList) > 0:
                avg_time = sum(pasttimeList) / len(pasttimeList)
                increase_percentage = 0.05  # increase the distance by 5% of the average distance
                increase_time = avg_time * increase_percentage
                new_time = avg_time + increase_time
                challenge['time'] = ceil(new_time)

changeChallengeParameters()
            
for index, challenge in RecChallenges.iterrows():
    string = challenge['challengesTemplate']
    for column in challenge.index:
        if '<' + column + '>' in challenge['challengesTemplate']:
            string = string.replace('<' + column + '>', str(challenge[column]))
    RecChallenges.loc[index, 'challengesTemplate'] = string


def chalOne(df):
    tempDF = RecChallenges.iloc[0].to_frame().T
    df = pd.concat([df, tempDF]).reset_index(drop=True)
    st.session_state['df'] = df

def chalTwo(df):
    tempDF = RecChallenges.iloc[1].to_frame().T
    df = pd.concat([df, tempDF]).reset_index(drop=True)
    st.session_state['df'] = df

def chalThree(df):
    tempDF = RecChallenges.iloc[2].to_frame().T
    df = pd.concat([df, tempDF]).reset_index(drop=True)
    st.session_state['df'] = df


header = st.title('Pick a challenge')
text = st.caption(method)

button1 = st.button(RecChallenges.loc[0,'challengesTemplate'],key='btn1', on_click=chalOne, args=(df,))

button2 = st.button(RecChallenges.loc[1,'challengesTemplate'],key='btn2', on_click=chalTwo, args=(df,))

button3 = st.button(RecChallenges.loc[2,'challengesTemplate'],key='btn3', on_click=chalThree, args=(df,))

st.dataframe(data=df)

