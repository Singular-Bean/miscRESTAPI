import json
import pulp
import http.client
import pandas as pd
from scipy.stats import binom
from safe_requests_misc import safeRequest
from benchWeightings import playedPercentageOutfield, playedPercentageGk

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)


connection = http.client.HTTPSConnection('fantasy.premierleague.com')

headers = {
    'x-api-authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImRlZmF1bHQifQ.eyJjbGllbnRfaWQiOiJiZmNiYWY2OS1hYWRlLTRjMWItOGYwMC1jMWNiOGExOTMwMzAiLCJpc3MiOiJodHRwczovL2F1dGgucGluZ29uZS5ldS82ODM0MGRlMS1kZmI5LTQxMmUtOTM3Yy0yMDE3Mjk4NmQxMjkvYXMiLCJqdGkiOiIwZjIyOGE0Mi1hNGY0LTQ3ZGQtYTkzOS0yZTgzM2I1Nzg0ZTYiLCJpYXQiOjE3OTMwMzMwMTQsImV4cCI6MTc5MzAzNjYxNCwiYXVkIjpbImh0dHBzOi8vYXBpLnBpbmdvbmUuZXUiXSwic2NvcGUiOiJpbnRlcmVzdCBvcGVuaWQgcDE6dXBkYXRlOnVzZXIgcHJvZmlsZSBjb25zZW50IGVtYWlsIiwic3ViIjoiNGZjNWZmZjctYTg4MS00ZGI1LWJlY2MtNDU4NDE5OTk1MDEwIiwic2lkIjoiMjFiYzNlODEtMTEzNC00OGY2LTg4YWUtM2MzZTMxOWQxMWI5IiwiYXV0aF90aW1lIjoxNzkyNzU0OTMyLCJhY3IiOiIyNjJjZTRiMDFkMTlkZDlkMzg1ZDI2YmRkYjQyOTdiNiIsImF1dGhlbnRpY2F0b3IiOiJwd2QiLCJodHRwOi8vbWVkaWFraW5kLmNvbS9tZi90aWQiOiJkZWZhdWx0IiwiZW52IjoiNjgzNDBkZTEtZGZiOS00MTJlLTkzN2MtMjAxNzI5ODZkMTI5Iiwib3JnIjoiM2E2ODUwMzItODMyNi00OTY5LWE3OGItY2MyOTc3NWIxM2Q2IiwicDEucmlkIjoiZjY0MzljMDktNjQ1My00NWMzLTk0ZDItZGRlMjkyMDJmMGEwIn0.MjyZFpEN4Bd9hMDucoFpgkBxMnX0SjzdmPHJ71FKb5BsxmJetS6Dic0YHc9ayxCYyX8mD6pkSmwy_xXd8UYato8AEio_9p-AsctdswTF5rJjEqoMsKRyNzKOu-Bg0boRcerznYnVfITOAK6V1KXbmM9AHkPz-qOQJNpnrG74Gi3Cf5VRxnUfzx-abgbkHrG8Brv647KKFsUO1CbSSacuj980v86LAL-H2DyNbD51egXAto0LqWYvkMmpJgReG1Kkzb6hIR4TcxfVEygITBcbj-pswleH_1NMf0gXexd8GrWAsUoThahNVPAtFE0uH0Jbk-aH3HvQGRCpgFCM7eS6WQ'
    }

qOutfield = 1 - playedPercentageOutfield

probSub1 = binom.sf(0, 10, qOutfield)
probSub2 = binom.sf(1, 10, qOutfield)
probSub3 = binom.sf(2, 10, qOutfield)
probSubGk = 1 - playedPercentageGk

print(f"Probability of 1 sub: {probSub1:.4f}, Probability of 2 subs: {probSub2:.4f}, Probability of 3 subs: {probSub3:.4f}, Probability of GK sub: {probSubGk:.4f}")

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


def optimiseFplSquad(playerData: pd.DataFrame, maxBudget: float = 1000.0, variable: str = 'selected_by_percent') -> pd.DataFrame:
    playerData[variable] = playerData[variable].astype(float)
    optimisationProblem = pulp.LpProblem("MaxSelectedPercentSquad", pulp.LpMaximize)
    playerVars = pulp.LpVariable.dicts("player", playerData.index, cat="Binary")

    optimisationProblem += pulp.lpSum(
        [float(playerData.loc[i, variable]) * playerVars[i] for i in playerData.index]
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
    playerData['selected_by_percent'] = playerData['selected_by_percent'].astype(float)
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

def getBenchAndCapitains(dfOg: pd.DataFrame):
    df = dfOg.copy()
    df['selected_by_percent'] = df['selected_by_percent'].astype(float)
    df.sort_values(by="selected_by_percent", inplace=True)
    benchNames = []
    benchTypes = []
    goalkeeper = []
    count = 0
    vice = None
    cap = None
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
        if count == 13:
            vice = index
        if count == 14:
            cap = index
        count += 1
    benchNames.reverse()
    benchNames = goalkeeper + benchNames
    print(f"\nBench: {benchNames}\nCaptain: {cap}\nVice Captain: {vice}")


allInfo = jsonRequest("/api/bootstrap-static/", cache_ttl=69)

playerInfos = allInfo["elements"]

playerDict = {}
for playerInfo in playerInfos:
    firstName = playerInfo.pop('first_name', None)
    secondName = playerInfo.pop('second_name', None)
    playerFullName = f"{firstName} {secondName}" if secondName is not None else firstName

    playerDict[playerFullName] = playerInfo

DF = pd.DataFrame(playerDict).T[['now_cost', 'element_type', 'selected_by_percent', 'team']]


currentTeamData = jsonRequest("/api/my-team/133766/", cache_ttl=69)
#currentTeamData = jsonRequest("/api/my-team/1320530/", cache_ttl=69)
picks = currentTeamData["picks"]
banked = currentTeamData["transfers"]['bank']
teamIds = []
sellingPrices = []
currentSquadSelectedPct = 0
for pick in picks:
    teamIds.append(pick['element'])
    sellingPrices.append(pick['selling_price'])
for player in playerDict.keys():
    if playerDict[player]['id'] in teamIds:
        currentSquadSelectedPct += float(playerDict[player]['selected_by_percent'])
        playerDict[player]['now_cost'] = sellingPrices[teamIds.index(playerDict[player]['id'])]

squadCurrentValue = sum(sellingPrices) + banked

DF2 = pd.DataFrame(playerDict).T[['now_cost', 'element_type', 'selected_by_percent', 'team', 'id']]
DF2.reset_index(names='playerName', inplace=True)
DF2.set_index('id', inplace=True)
overallOptimalSquad = optimiseFplSquad(DF, maxBudget=1000.0).sort_values(by=["element_type", 'selected_by_percent'], ascending=[True, False])
print(overallOptimalSquad)


currentTeamList = []
for id in teamIds:
    currentTeamList.append(DF2.loc[id, "playerName"])

optimisedTeam = optimiseWithTransfers(DF2, teamIds, 15, maxBudget=squadCurrentValue).sort_values(by=["element_type", 'selected_by_percent'], ascending=[True, False])
optimisedTeam.set_index('playerName', inplace=True)
optimisedTeam.index.name = None
print(optimisedTeam)
getBenchAndCapitains(optimisedTeam)
print(f"\nCurrent Squad Aggregate Selected Percentage: {currentSquadSelectedPct:.1f}")
print(f"\nOptimal Squad Aggregate Selected Percentage: {sum(optimisedTeam['selected_by_percent'].astype(float)):.1f}")
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

print("\nDifference from most optimal £100M squad:")
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