# Boring FPL

This is a Python script which fetches data from the Fantasy Premier League API and performs a constrained
optimisation to select a valid team of 15 players which maximises the % owned metric among the players, effectively
making the most owned/most boring team possible.

Below is an example output (date: 27/10/26):

```
                               now_cost  element_type  selected_by_percent  team     role     captaincy
David Raya Martín                    62             1                 45.7     1  Starter              
Riccardo Calafiori                   60             2                 52.3     1  Starter              
Maxim De Cuyper                      53             2                 42.6     5  Starter              
Joško Gvardiol                       57             2                 27.0    15  Starter              
Lewis Hall                           53             2                 20.5    17  Starter              
Morgan Rogers                        80             3                 50.1     6  Starter              
Pascal Groß                          62             3                 46.4     5  Starter              
Rayan Cherki                         80             3                 38.6    15  Starter              
Erling Haaland                      157             4                 78.0    15  Starter       Captain
João Pedro Junqueira de Jesus        79             4                 70.7     6  Starter  Vice Captain
Dominic Calvert-Lewin                61             4                 21.4    13  Starter              
Ezri Konsa Ngoyo                     47             2                 20.0     1    Sub 1              
Marcus Tavernier                     64             3                 18.0     3    Sub 2              
Will Hughes                          43             3                  6.0     8    Sub 3              
Martin Dubravka                      40             1                 16.1    19   Sub GK               
```

## Bench Weightings

When players are selecting their squad, they often put more importance on the starting 11 than the bench players, so
this is something I wanted to incorporate into the programme. I used Vaastav's FPL GitHub dataset to obtain historical
FPL data going back to the start of the 22/23 season. From this I was able to get the probability that a player in the
top 35 most owned players (of that game week) would be automatically substituted out (not play any minutes in a game
week), which turned out to be roughly 11%. Using this, I was able to calculate the probability of each slot on the bench
being substituted in, using binomial probability. I then did the same thing for goalkeepers because one of the bench
slots is saved for a goalie. This ended up being just below 5%. Once I had these weights, I was able to modify the
optimisation to assign players slots on the bench, those players' % owned was then multiplied by the probability of them
being substituted in. This effectively tells the model to place more importance on the starting 11, but uses
mathematically sound reasoning to determine how much importance to place on the bench players.

Using this I was able to create a modified version of the function which fetches an existing FPL team and the number of
transfers allowed, and maximises % owned based on those restrictions as well.

Here is an example output of the modified function, when limited to 3 transfers (date: 27/10/26):

```
                               now_cost  element_type  selected_by_percent  team     role     captaincy
David Raya Martín                    61             1                 45.7     1  Starter              
Riccardo Calafiori                   57             2                 52.3     1  Starter              
Maxim De Cuyper                      50             2                 42.6     5  Starter              
Joško Gvardiol                       57             2                 27.0    15  Starter              
Morgan Rogers                        78             3                 50.1     6  Starter              
Pascal Groß                          59             3                 46.4     5  Starter              
Rayan Cherki                         79             3                 38.6    15  Starter              
Cole Palmer                          98             3                 27.5     6  Starter              
Erling Haaland                      156             4                 78.0    15  Starter       Captain
João Pedro Junqueira de Jesus        77             4                 70.7     6  Starter  Vice Captain
Dominic Calvert-Lewin                60             4                 21.4    13  Starter              
Ezri Konsa Ngoyo                     46             2                 20.1     1    Sub 1              
Semi Ajayi                           42             2                 13.0    11    Sub 2              
Will Hughes                          43             3                  6.0     8    Sub 3              
Martin Dubravka                      40             1                 16.1    19   Sub GK              

Current Squad Weighted Aggregate Selected Percentage: 514.1

Optimal Squad Weighted Aggregate Selected Percentage: 519.6

Out:
Lewis Hall
Dominik Szoboszlai
Kevin Schade

In:
Cole Palmer
Semi Ajayi
Will Hughes

Difference from most optimal £100M squad:

Out:
Cole Palmer
Semi Ajayi

In:
Lewis Hall
Marcus Tavernier
```

As you can see, it states the transfers that could be made, the change in weighted aggregate selected percentage between
the user's current squad and their squad after making those transfers, and the difference between the user's squad after
making those transfers and the most optimal £100M squad possible.

In this instance the differences between this squad and the most optimal are only there because this user has a total
squad value of more than £100M, whereas the first squad is limited to £100M.

In theory this mechanism can be used in combination with any given metric. For example, total points, player form,
transfers in/out, or even an entirely new metric.