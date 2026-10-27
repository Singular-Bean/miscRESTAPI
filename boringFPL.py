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
    'x-api-authorization': 'Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImRlZmF1bHQifQ.eyJjbGllbnRfaWQiOiJiZmNiYWY2OS1hYWRlLTRjMWItOGYwMC1jMWNiOGExOTMwMzAiLCJpc3MiOiJodHRwczovL2F1dGgucGluZ29uZS5ldS82ODM0MGRlMS1kZmI5LTQxMmUtOTM3Yy0yMDE3Mjk4NmQxMjkvYXMiLCJqdGkiOiIxNmRhYjI4NC1hNjUzLTQxZDItYjc0NC1jYjg2NTdjMjQ1NTgiLCJpYXQiOjE3OTMxMDIwNzQsImV4cCI6MTc5MzEwNTY3NCwiYXVkIjpbImh0dHBzOi8vYXBpLnBpbmdvbmUuZXUiXSwic2NvcGUiOiJpbnRlcmVzdCBvcGVuaWQgcDE6dXBkYXRlOnVzZXIgcHJvZmlsZSBjb25zZW50IGVtYWlsIiwic3ViIjoiNGZjNWZmZjctYTg4MS00ZGI1LWJlY2MtNDU4NDE5OTk1MDEwIiwic2lkIjoiMjFiYzNlODEtMTEzNC00OGY2LTg4YWUtM2MzZTMxOWQxMWI5IiwiYXV0aF90aW1lIjoxNzkyNzU0OTMyLCJhY3IiOiIyNjJjZTRiMDFkMTlkZDlkMzg1ZDI2YmRkYjQyOTdiNiIsImF1dGhlbnRpY2F0b3IiOiJwd2QiLCJodHRwOi8vbWVkaWFraW5kLmNvbS9tZi90aWQiOiJkZWZhdWx0IiwiZW52IjoiNjgzNDBkZTEtZGZiOS00MTJlLTkzN2MtMjAxNzI5ODZkMTI5Iiwib3JnIjoiM2E2ODUwMzItODMyNi00OTY5LWE3OGItY2MyOTc3NWIxM2Q2IiwicDEucmlkIjoiZjY0MzljMDktNjQ1My00NWMzLTk0ZDItZGRlMjkyMDJmMGEwIn0.VdWt3AucuxglbL6GLBeMoDNORVNlWf652G6sBc9V94CLS7KpXKL80Yn33KY4ccQEYyl9d9uFLymndOXxmm_CkBiJ4OlH-KjeVR8lTw3F51pNJhqLI70KiPnyGdOMkP8miwE_iTFnZEWRtGgdWF-B5vpbseCNRWK65qJLrmyHdokADk2Qn8Ir7nxxGGm7UDQje9lJAQEhMZbDYwxANmaWj-qfWTQ7ufIZh4Z-aE0E05RgpRedvktWzjXIsVyMC24g6D8yjzBR49BMd8g2s5QgSbjU3w1ob-rvoiDZN1Fwh_z1dFD2lWmJwR1tiHFtA82ksVQX2BCjLvSdinsfprqlOQ'
    }

qOutfield = 1 - playedPercentageOutfield

probSub1 = binom.sf(0, 10, qOutfield)
probSub2 = binom.sf(1, 10, qOutfield)
probSub3 = binom.sf(2, 10, qOutfield)
probSubGk = 1 - playedPercentageGk

weightingMap = [1,1,1,1,1,1,1,1,1,1,1,probSubGk,probSub1,probSub2,probSub3]
weightingMap2 = [1,1,1,1,1,1,1,1,1,1,1,probSub1,probSub2,probSub3,probSubGk]

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


def optimiseFplSquadWeighted(playerData: pd.DataFrame, maxBudget: float = 1000.0,
                             variable: str = 'selected_by_percent') -> pd.DataFrame:
    playerData[variable] = playerData[variable].astype(float)
    optimisationProblem = pulp.LpProblem("MaxWeightedSquad", pulp.LpMaximize)

    # Define role-based binary decision variables for each player
    starterVars = pulp.LpVariable.dicts("starter", playerData.index, cat="Binary")
    sub1Vars = pulp.LpVariable.dicts("sub1", playerData.index, cat="Binary")
    sub2Vars = pulp.LpVariable.dicts("sub2", playerData.index, cat="Binary")
    sub3Vars = pulp.LpVariable.dicts("sub3", playerData.index, cat="Binary")
    subGkVars = pulp.LpVariable.dicts("subGk", playerData.index, cat="Binary")

    # Assign calculated weights
    wStarter = 1.0
    wSub1 = probSub1
    wSub2 = probSub2
    wSub3 = probSub3
    wSubGk = probSubGk

    # Objective function incorporating bench-activation weights
    optimisationProblem += pulp.lpSum([
        float(playerData.loc[i, variable]) * (
                wStarter * starterVars[i] +
                wSub1 * sub1Vars[i] +
                wSub2 * sub2Vars[i] +
                wSub3 * sub3Vars[i] +
                wSubGk * subGkVars[i]
        ) for i in playerData.index
    ])

    # Budget constraint across all 15 squad slots
    optimisationProblem += pulp.lpSum([
        playerData.loc[i, "now_cost"] * (
                starterVars[i] + sub1Vars[i] + sub2Vars[i] + sub3Vars[i] + subGkVars[i]
        ) for i in playerData.index
    ]) <= maxBudget

    # Mutual exclusivity: a player can hold at most one role
    for i in playerData.index:
        optimisationProblem += (
                starterVars[i] + sub1Vars[i] + sub2Vars[i] + sub3Vars[i] + subGkVars[i] <= 1
        )

    # Total positional squad constraints (2 GK, 5 DEF, 5 MID, 3 FWD)
    for pos, count in [(1, 2), (2, 5), (3, 5), (4, 3)]:
        optimisationProblem += pulp.lpSum([
            starterVars[i] + sub1Vars[i] + sub2Vars[i] + sub3Vars[i] + subGkVars[i]
            for i in playerData.index if playerData.loc[i, "element_type"] == pos
        ]) == count

    # Exact slot counts for starters and bench positions
    optimisationProblem += pulp.lpSum([starterVars[i] for i in playerData.index]) == 11
    optimisationProblem += pulp.lpSum([sub1Vars[i] for i in playerData.index]) == 1
    optimisationProblem += pulp.lpSum([sub2Vars[i] for i in playerData.index]) == 1
    optimisationProblem += pulp.lpSum([sub3Vars[i] for i in playerData.index]) == 1
    optimisationProblem += pulp.lpSum([subGkVars[i] for i in playerData.index]) == 1

    # Goalkeeper specific role constraints
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 1]) == 1
    optimisationProblem += pulp.lpSum(
        [subGkVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 1]) == 1

    # Starting formation boundary constraints (valid FPL formations)
    # Def starters: 3 to 5
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 2]) >= 3
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 2]) <= 5

    # Mid starters: 2 to 5
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 3]) >= 2
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 3]) <= 5

    # Fwd starters: 1 to 3
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 4]) >= 1
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 4]) <= 3

    # Club restriction (max 3 players per club across the entire squad)
    uniqueClubs = playerData["team"].unique()
    for club in uniqueClubs:
        optimisationProblem += pulp.lpSum([
            starterVars[i] + sub1Vars[i] + sub2Vars[i] + sub3Vars[i] + subGkVars[i]
            for i in playerData.index if playerData.loc[i, "team"] == club
        ]) <= 3

    optimisationProblem.solve(pulp.PULP_CBC_CMD(msg=False))

    # Compile the selected squad and assign their determined roles
    squadData = []
    for i in playerData.index:
        assignedRole = None
        if starterVars[i].varValue and starterVars[i].varValue > 0.5:
            assignedRole = "Starter"
        elif sub1Vars[i].varValue and sub1Vars[i].varValue > 0.5:
            assignedRole = "Sub 1"
        elif sub2Vars[i].varValue and sub2Vars[i].varValue > 0.5:
            assignedRole = "Sub 2"
        elif sub3Vars[i].varValue and sub3Vars[i].varValue > 0.5:
            assignedRole = "Sub 3"
        elif subGkVars[i].varValue and subGkVars[i].varValue > 0.5:
            assignedRole = "Sub GK"

        if assignedRole:
            rowCopy = playerData.loc[i].copy()
            rowCopy['role'] = assignedRole
            squadData.append(rowCopy)

    # Assign captaincy and vice-captaincy based on the highest selected_by_percent values
    df = pd.DataFrame(squadData)
    df['captaincy'] = ''
    df.loc[df['selected_by_percent'].nlargest(2).index, 'captaincy'] = ['Captain', 'Vice Captain']
    return df


def optimiseWithTransfersWeighted(playerData: pd.DataFrame, currentSquadIds: list, allowedTransfers: int,
                                  maxBudget: float = 1000.0, variable: str = 'selected_by_percent') -> pd.DataFrame:
    playerData[variable] = playerData[variable].astype(float)
    optimisationProblem = pulp.LpProblem("MaxWeightedSquadWithTransfers", pulp.LpMaximize)

    # Define role-based binary decision variables for each player
    starterVars = pulp.LpVariable.dicts("starter", playerData.index, cat="Binary")
    sub1Vars = pulp.LpVariable.dicts("sub1", playerData.index, cat="Binary")
    sub2Vars = pulp.LpVariable.dicts("sub2", playerData.index, cat="Binary")
    sub3Vars = pulp.LpVariable.dicts("sub3", playerData.index, cat="Binary")
    subGkVars = pulp.LpVariable.dicts("subGk", playerData.index, cat="Binary")

    # Assign calculated weights
    wStarter = 1.0
    wSub1 = probSub1
    wSub2 = probSub2
    wSub3 = probSub3
    wSubGk = probSubGk

    # Objective function incorporating bench-activation weights
    optimisationProblem += pulp.lpSum([
        float(playerData.loc[i, variable]) * (
                wStarter * starterVars[i] +
                wSub1 * sub1Vars[i] +
                wSub2 * sub2Vars[i] +
                wSub3 * sub3Vars[i] +
                wSubGk * subGkVars[i]
        ) for i in playerData.index
    ])

    # Budget constraint across all 15 squad slots
    optimisationProblem += pulp.lpSum([
        playerData.loc[i, "now_cost"] * (
                starterVars[i] + sub1Vars[i] + sub2Vars[i] + sub3Vars[i] + subGkVars[i]
        ) for i in playerData.index
    ]) <= maxBudget

    # Mutual exclusivity: a player can hold at most one role
    for i in playerData.index:
        optimisationProblem += (
                starterVars[i] + sub1Vars[i] + sub2Vars[i] + sub3Vars[i] + subGkVars[i] <= 1
        )

    # Total positional squad constraints (2 GK, 5 DEF, 5 MID, 3 FWD)
    for pos, count in [(1, 2), (2, 5), (3, 5), (4, 3)]:
        optimisationProblem += pulp.lpSum([
            starterVars[i] + sub1Vars[i] + sub2Vars[i] + sub3Vars[i] + subGkVars[i]
            for i in playerData.index if playerData.loc[i, "element_type"] == pos
        ]) == count

    # Exact slot counts for starters and bench positions
    optimisationProblem += pulp.lpSum([starterVars[i] for i in playerData.index]) == 11
    optimisationProblem += pulp.lpSum([sub1Vars[i] for i in playerData.index]) == 1
    optimisationProblem += pulp.lpSum([sub2Vars[i] for i in playerData.index]) == 1
    optimisationProblem += pulp.lpSum([sub3Vars[i] for i in playerData.index]) == 1
    optimisationProblem += pulp.lpSum([subGkVars[i] for i in playerData.index]) == 1

    # Goalkeeper specific role constraints
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 1]) == 1
    optimisationProblem += pulp.lpSum(
        [subGkVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 1]) == 1

    # Starting formation boundary constraints (valid FPL formations)
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 2]) >= 3
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 2]) <= 5

    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 3]) >= 2
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 3]) <= 5

    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 4]) >= 1
    optimisationProblem += pulp.lpSum(
        [starterVars[i] for i in playerData.index if playerData.loc[i, "element_type"] == 4]) <= 3

    # Club restriction (max 3 players per club across the entire squad)
    uniqueClubs = playerData["team"].unique()
    for club in uniqueClubs:
        optimisationProblem += pulp.lpSum([
            starterVars[i] + sub1Vars[i] + sub2Vars[i] + sub3Vars[i] + subGkVars[i]
            for i in playerData.index if playerData.loc[i, "team"] == club
        ]) <= 3

    # Transfer constraint: retained players from currentSquadIds must be at least (15 - allowedTransfers)
    optimisationProblem += pulp.lpSum([
        starterVars[i] + sub1Vars[i] + sub2Vars[i] + sub3Vars[i] + subGkVars[i]
        for i in currentSquadIds if i in playerData.index
    ]) >= (15 - allowedTransfers)

    optimisationProblem.solve(pulp.PULP_CBC_CMD(msg=False))

    # Compile the selected squad and assign their determined roles
    squadData = []
    for i in playerData.index:
        assignedRole = None
        if starterVars[i].varValue and starterVars[i].varValue > 0.5:
            assignedRole = "Starter"
        elif sub1Vars[i].varValue and sub1Vars[i].varValue > 0.5:
            assignedRole = "Sub 1"
        elif sub2Vars[i].varValue and sub2Vars[i].varValue > 0.5:
            assignedRole = "Sub 2"
        elif sub3Vars[i].varValue and sub3Vars[i].varValue > 0.5:
            assignedRole = "Sub 3"
        elif subGkVars[i].varValue and subGkVars[i].varValue > 0.5:
            assignedRole = "Sub GK"

        if assignedRole:
            rowCopy = playerData.loc[i].copy()
            rowCopy['role'] = assignedRole
            squadData.append(rowCopy)

    # Assign captaincy and vice-captaincy based on the highest selected_by_percent values
    df = pd.DataFrame(squadData)
    df['captaincy'] = ''
    df.loc[df['selected_by_percent'].nlargest(2).index, 'captaincy'] = ['Captain', 'Vice Captain']
    return df


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
        currentSquadSelectedPct += float(playerDict[player]['selected_by_percent'])*(weightingMap[teamIds.index(playerDict[player]['id'])])
        playerDict[player]['now_cost'] = sellingPrices[teamIds.index(playerDict[player]['id'])]

squadCurrentValue = sum(sellingPrices) + banked

DF2 = pd.DataFrame(playerDict).T[['now_cost', 'element_type', 'selected_by_percent', 'team', 'id']]
DF2.reset_index(names='playerName', inplace=True)
DF2.set_index('id', inplace=True)
overallOptimalSquad = optimiseFplSquadWeighted(DF, maxBudget=1000.0).sort_values(by=["role", "element_type", 'selected_by_percent'], ascending=[True, True, False])
print(overallOptimalSquad, "\n\n")


currentTeamList = []
for id in teamIds:
    currentTeamList.append(DF2.loc[id, "playerName"])

optimisedTeam = optimiseWithTransfersWeighted(DF2, teamIds, 15, maxBudget=squadCurrentValue).sort_values(by=["role", "element_type", 'selected_by_percent'], ascending=[True, True, False])
optimisedTeam.set_index('playerName', inplace=True)
optimisedTeam.index.name = None
print(optimisedTeam)

aggSelectedPct = 0
for x in optimisedTeam['selected_by_percent'].astype(float):
    weightedPct = x*weightingMap2[optimisedTeam.index.get_loc(optimisedTeam.index[optimisedTeam['selected_by_percent'].astype(float) == x][0])]
    aggSelectedPct += weightedPct

print(f"\nCurrent Squad Weighted Aggregate Selected Percentage: {currentSquadSelectedPct:.1f}")
print(f"\nOptimal Squad Weighted Aggregate Selected Percentage: {aggSelectedPct:.1f}")

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