import json
import pulp
import http.client
import pandas as pd
from safe_requests_misc import safeRequest

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)


connection = http.client.HTTPSConnection('fantasy.premierleague.com')

headers = {
    'x-api-authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImRlZmF1bHQifQ.eyJjbGllbnRfaWQiOiJiZmNiYWY2OS1hYWRlLTRjMWItOGYwMC1jMWNiOGExOTMwMzAiLCJpc3MiOiJodHRwczovL2FjY291bnQucHJlbWllcmxlYWd1ZS5jb20vYXMiLCJqdGkiOiIyNzkxZmVkNi0yNDk1LTQ0ZGMtYWRlZi1hNTYxNWQ4ZmQ4ZjIiLCJpYXQiOjE3ODYzMTQzOTIsImV4cCI6MTc4NjM0MzE5MiwiYXVkIjpbImh0dHBzOi8vYXBpLnBpbmdvbmUuZXUiXSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsInN1YiI6IjRmYzVmZmY3LWE4ODEtNGRiNS1iZWNjLTQ1ODQxOTk5NTAxMCIsInNpZCI6ImVhZjBkZDJmLTRjMDUtNDQzZC05YWJkLWRmODIxZTM1ZWQwMiIsImF1dGhfdGltZSI6MTc4NTI1NDMzNywiYWNyIjoiMjYyY2U0YjAxZDE5ZGQ5ZDM4NWQyNmJkZGI0Mjk3YjYiLCJhdXRoZW50aWNhdG9yIjoicHdkIiwiaHR0cDovL21lZGlha2luZC5jb20vbWYvdGlkIjoiZGVmYXVsdCIsImVudiI6IjY4MzQwZGUxLWRmYjktNDEyZS05MzdjLTIwMTcyOTg2ZDEyOSIsIm9yZyI6IjNhNjg1MDMyLTgzMjYtNDk2OS1hNzhiLWNjMjk3NzViMTNkNiIsInAxLnJpZCI6IjNkMGY3ZmE3LTM5NjItNDkwOC04NmMxLTNlNWViZGFhMGMxYiJ9.NEEiLF5idp-DCBWSDVbuXxMEa8RLIXfd-pTx9fXDicQGjgjwTXSCXH0soKx-j0g8qiabEWXqn2dqKKnhMAzXLWQnwSrywcibxqK7QKhc19aGpO8CNHnPnPW09Q1KdBh5AkJc_yQp66hIIe7_7zDH4JO0zK4oasNd0d59Yt9Qxz1A0QvJl1jW_oHLTA4tn49ltrFPfwjOuTVTvmMFYtQCXwWX6C0oMrZzOGAEaxTp0j-Tlbt-J09kAEItiDzv6FoMGbp8bfBfsOzy0tmatrFCqbcjDd8wT6EtyHKR1srTMEnJ7KuqBeQQhefnPS-tjBX7No1W95QPgROo8dEKcw8VtA'
    }


def jsonRequest(url, cache_ttl=None, permanent=None):
    if cache_ttl is None:
        resp = safeRequest(url, headers=headers, permanent=permanent, connection=connection)
    elif cache_ttl == 69:
        cache_ttl = 1
        resp = safeRequest(url, headers=headers, ttl=cache_ttl, permanent=permanent, connection=connection)
    else:
        cache_ttl = cache_ttl * 3600
        resp = safeRequest(url, headers=headers , ttl=cache_ttl, permanent=permanent, connection=connection)
    return json.loads(resp.text)


def optimiseFplSquad(playerData: pd.DataFrame, maxBudget: float = 1000.0) -> pd.DataFrame:
    optimisationProblem = pulp.LpProblem("MaxSelectedPercentSquad", pulp.LpMaximize)
    playerVars = pulp.LpVariable.dicts("player", playerData.index, cat="Binary")

    optimisationProblem += pulp.lpSum(
        [float(playerData.loc[i, "selected_by_percent"]) * playerVars[i] for i in playerData.index]
    )

    optimisationProblem += pulp.lpSum(
        [playerData.loc[i, "now_cost"] * playerVars[i] for i in playerData.index]
    ) <= maxBudget

    optimisationProblem += pulp.lpSum(
        [playerVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 1]
    ) == 2

    optimisationProblem += pulp.lpSum(
        [playerVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 2]
    ) == 5

    optimisationProblem += pulp.lpSum(
        [playerVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 3]
    ) == 5

    optimisationProblem += pulp.lpSum(
        [playerVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 4]
    ) == 3

    uniqueClubs = playerData["team"].unique()
    for club in uniqueClubs:
        optimisationProblem += pulp.lpSum(
            [playerVars[i] for i in playerData.index if playerData.loc[i, "team"] == club]
        ) <= 3

    optimisationProblem.solve(pulp.PULP_CBC_CMD(msg=False))

    selectedIndices = [i for i in playerData.index if playerVars[i].varValue == 1.0]

    return playerData.loc[selectedIndices]


def optimiseWithTransfers(playerData: pd.DataFrame, currentSquadIds: list, allowedTransfers: int,
                          maxBudget: float = 1000.0) -> pd.DataFrame:
    optimisationProblem = pulp.LpProblem("MaxSelectedPercentWithTransfers", pulp.LpMaximize)
    playerVars = pulp.LpVariable.dicts("player", playerData.index, cat="Binary")

    optimisationProblem += pulp.lpSum(
        [float(playerData.loc[i, "selected_by_percent"]) * playerVars[i] for i in playerData.index]
    )

    optimisationProblem += pulp.lpSum(
        [playerData.loc[i, "now_cost"] * playerVars[i] for i in playerData.index]
    ) <= maxBudget

    optimisationProblem += pulp.lpSum(
        [playerVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 1]
    ) == 2

    optimisationProblem += pulp.lpSum(
        [playerVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 2]
    ) == 5

    optimisationProblem += pulp.lpSum(
        [playerVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 3]
    ) == 5

    optimisationProblem += pulp.lpSum(
        [playerVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 4]
    ) == 3

    uniqueClubs = playerData["team"].unique()
    for club in uniqueClubs:
        optimisationProblem += pulp.lpSum(
            [playerVars[i] for i in playerData.index if playerData.loc[i, "team"] == club]
        ) <= 3

    optimisationProblem += pulp.lpSum(
        [playerVars[i] for i in currentSquadIds if i in playerData.index]
    ) >= (15 - allowedTransfers)

    optimisationProblem.solve(pulp.PULP_CBC_CMD(msg=False))

    selectedIndices = [i for i in playerData.index if playerVars[i].varValue == 1.0]

    return playerData.loc[selectedIndices]

def getBench(dfOg: pd.DataFrame):
    df = dfOg.copy()
    df.sort_values(by="selected_by_percent", inplace=True)
    benchNames = []
    benchTypes = []
    goalkeeper = []
    for index, row in df.iterrows():
        if row['element_type'] == 1 and len(goalkeeper) < 1:
            goalkeeper.append(index)
        elif row['element_type'] == 2 and benchTypes.count(2) < 2 and len(benchNames) < 3:
            benchNames.append(index)
            benchTypes.append(2)
        elif row['element_type'] == 3 and benchTypes.count(3) < 3 and len(benchNames) < 3:
            benchNames.append(index)
            benchTypes.append(3)
        elif row['element_type'] == 4 and benchTypes.count(4) < 2 and len(benchNames) < 3:
            benchNames.append(index)
            benchTypes.append(4)
    benchNames.reverse()
    benchNames = goalkeeper + benchNames
    print(f"\nBench: {benchNames}")


allInfo = jsonRequest("/api/bootstrap-static/", cache_ttl=1)

playerInfos = allInfo["elements"]

playerDict = {}
for playerInfo in playerInfos:
    firstName = playerInfo.pop('first_name', None)
    secondName = playerInfo.pop('second_name', None)
    playerFullName = f"{firstName} {secondName}" if secondName is not None else firstName

    playerDict[playerFullName] = playerInfo

DF = pd.DataFrame(playerDict).T[['now_cost', 'element_type', 'selected_by_percent', 'team']]


currentTeamData = jsonRequest("/api/my-team/133766/", cache_ttl=69)
picks = currentTeamData["picks"]
banked = currentTeamData["transfers"]['bank']
teamIds = []
sellingPrices = []
for pick in picks:
    teamIds.append(pick['element'])
    sellingPrices.append(pick['selling_price'])
for player in playerDict.keys():
    if playerDict[player]['id'] in teamIds:
        playerDict[player]['now_cost'] = sellingPrices[teamIds.index(playerDict[player]['id'])]

squadCurrentValue = sum(sellingPrices) + banked

DF2 = pd.DataFrame(playerDict).T[['now_cost', 'element_type', 'selected_by_percent', 'team', 'id']]
DF2.reset_index(names='playerName', inplace=True)
DF2.set_index('id', inplace=True)
overallOptimalSquad = optimiseFplSquad(DF, maxBudget=1000.0).sort_values(by="element_type")
print(overallOptimalSquad)


currentTeamList = []
for id in teamIds:
    currentTeamList.append(DF2.loc[id, "playerName"])

optimisedTeam = optimiseWithTransfers(DF2, teamIds, 15, maxBudget=squadCurrentValue).sort_values(by="element_type")
optimisedTeam.set_index('playerName', inplace=True)
optimisedTeam.index.name = None
print(optimisedTeam)
getBench(optimisedTeam)
newTeamList = []
optimalSquadList = []
for player in optimisedTeam.index:
    newTeamList.append(player)
for player in overallOptimalSquad.index:
    optimalSquadList.append(player)
print("\nOut:")
switch = True
for player in currentTeamList:
    if player not in newTeamList:
        print(player)
        switch = False
if switch:
    print(None)
print("\nIn:")
for player in newTeamList:
    if player not in currentTeamList:
        print(player)
if switch:
    print(None)

print("\nDifference from most optimal squad:")
print("\nOut:")
switch = True
for player in newTeamList:
    if player not in optimalSquadList:
        print(player)
        switch = False
if switch:
    print(None)
print("\nIn:")
for player in optimalSquadList:
    if player not in newTeamList:
        print(player)
if switch:
    print(None)