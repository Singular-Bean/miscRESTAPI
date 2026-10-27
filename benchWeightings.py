import pandas as pd
import numpy as np

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

neededColumns = ['position', 'GW', 'name', 'starts', 'minutes', 'selected']

printText = False

def printIf(string):
    if printText:
        print(string)

def transformGkDf(df):
    gk_df = df[df['position'] == 'GK']
    gk_df['gameweeksNumber'] = gk_df['GW'].nunique()
    gk_df['minimumStarts'] = (gk_df['gameweeksNumber']/2).astype(int)
    gk_df['totalStarts'] = gk_df.groupby('name')['starts'].transform('sum')
    gk_df['startingGk'] = (gk_df['totalStarts'] >= gk_df['minimumStarts']).astype(int)
    return gk_df[gk_df['startingGk'] == 1]

filepaths = ['data/merged_gw_22_23.csv', 'data/merged_gw_23_24.csv', 'data/merged_gw_24_25.csv', 'data/merged_gw_25_26.csv', 'data/merged_gw_26_27.csv']

for filepath in filepaths:
    index = filepaths.index(filepath)
    df = pd.read_csv(filepath)
    df['GW'] += (38*(index))


    outfield_df = df[df['position'] != 'GK']

    gk_df = transformGkDf(df)
    printIf(gk_df)

    if index == 0:
        totalOutfield_df = outfield_df[neededColumns]
        totalGk_df = gk_df[neededColumns]
    else:
        totalOutfield_df = pd.concat([totalOutfield_df, outfield_df[neededColumns]], ignore_index=True)
        totalGk_df = pd.concat([totalGk_df, gk_df[neededColumns]], ignore_index=True)

printIf(totalOutfield_df)
printIf(totalGk_df)

totalPlayed = 0
totalNotPlayed = 0
totalPlayedGk = 0
totalNotPlayedGk = 0

for gw, group in totalOutfield_df.groupby('GW'):
    # Top 40 outfield players by selection
    top_outfield = group[group['position'] != 'GK'].nlargest(35, 'selected')
    top_outfield['played'] = (top_outfield['minutes'] > 0).astype(int)
    printIf(top_outfield.sort_values(by='selected', ascending=False)[['name', 'selected', 'played']])
    totalPlayed += top_outfield['played'].sum()
    totalNotPlayed += (35 - top_outfield['played'].sum())

for gw, group in totalGk_df.groupby('GW'):
    top_gk = group[group['position'] == 'GK'].nlargest(5, 'selected')
    top_gk['played'] = (top_gk['minutes'] > 0).astype(int)
    printIf(top_gk.sort_values(by='selected', ascending=False)[['name', 'selected', 'played']])
    totalPlayedGk += top_gk['played'].sum()
    totalNotPlayedGk += (5 - top_gk['played'].sum())

printIf(f"Total played: {totalPlayed}")
printIf(f"Total not played: {totalNotPlayed}")
playedPercentageOutfield = totalPlayed/(totalPlayed+totalNotPlayed)
printIf(f"Percentage: {playedPercentageOutfield*100:.2f}%")

printIf(f"Total played GK: {totalPlayedGk}")
printIf(f"Total not played GK: {totalNotPlayedGk}")
playedPercentageGk = totalPlayedGk/(totalPlayedGk+totalNotPlayedGk)
printIf(f"Percentage GK: {playedPercentageGk*100:.2f}%")