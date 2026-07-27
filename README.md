# Boring FPL:

This is a simple Python script which fetches data from the Fantasy Premier League API and performs a constrained optimisation to select a valid team of 15 players which maximises the % owned metric among the players, effectively making the most owned/most boring team possible.

Below is an example output (date: 27/07/26):

```
                              now_cost element_type selected_by_percent team
David Raya Martín                   60            1                29.7    1
Martin Dubravka                     40            1                24.8   19
Milan van Ewijk                     40            2                17.0    7
Issa Diop                           40            2                21.3   12
Marc Guéhi                          60            2                25.0   15
Luke Shaw                           45            2                20.9   16
Pedro Porro Sauceda                 55            2                23.9   19
Morgan Rogers                       75            3                33.9    6
Will Hughes                         45            3                10.1    8
Iliman Ndiaye                       60            3                21.3    9
Dominik Szoboszlai                  70            3                45.5   14
Bruno Borges Fernandes             120            3                48.8   16
João Pedro Junqueira de Jesus       75            4                48.7    6
Erling Haaland                     155            4                74.9   15
Brian Brobbey                       60            4                22.6   20
```

Using this I was able to create a modified version of the function which fetches an existing FPL team and the number of transfers allowed, and maximises % owned based on those restrictions as well.

Because the season hasn't started yet, there is no limit on transfers, but here is an output when restricted to 3 transfers (performed on a team created by just using the "auto-pick" feature):

```
                                 now_cost element_type selected_by_percent team
Caoimhín Kelleher                      50            1                 5.6    4
Martin Dubravka                        40            1                24.8   19
Trevoh Chalobah                        55            2                 2.1    6
Rúben dos Santos Gato Alves Dias       55            2                 1.3   15
Nikola Milenković                      55            2                 2.3   18
Pedro Porro Sauceda                    55            2                23.9   19
Nordi Mukiele                          55            2                 8.2   20
Morgan Rogers                          75            3                33.9    6
Dominik Szoboszlai                     70            3                45.5   14
Phil Foden                             70            3                 5.3   15
Bruno Borges Fernandes                120            3                48.8   16
Bruno Guimarães Rodriguez Moura        70            3                 8.2   17
Kai Havertz                            75            4                 4.3    1
Igor Thiago Nascimento Rodrigues       80            4                16.7    4
João Pedro Junqueira de Jesus          75            4                48.7    6

Out:
Rayan Aït-Nouri
Cody Gakpo
Bernd Leno

In:
Martin Dubravka
Pedro Porro Sauceda
Morgan Rogers

Difference from most optimal squad:

Out:
Caoimhín Kelleher
Trevoh Chalobah
Rúben dos Santos Gato Alves Dias
Nikola Milenković
Nordi Mukiele
Phil Foden
Bruno Guimarães Rodriguez Moura
Kai Havertz
Igor Thiago Nascimento Rodrigues

In:
David Raya Martín
Milan van Ewijk
Issa Diop
Marc Guéhi
Luke Shaw
Will Hughes
Iliman Ndiaye
Erling Haaland
Brian Brobbey
```

As you can see, it states the transfers that could be made, and also shows how far away the remaining squad is from the current most owned squad.

I am already aware of a way I can modify the programme to automatically detect how many transfers a user is able to make, but the information is only available once the season has started.

In theory this mechanism can be used in combination with any given metric. For example, total points, player form, transfers in/out, or even an entirely new metric.