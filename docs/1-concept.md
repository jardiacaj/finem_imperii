
# Concept

By Joan Ardiaca Jové.

## Contents:
1. Game idea
2. Conceptualization
3. Development
4. Roadmap

---

# Game idea

Finem Imperii is a web-based role-strategy multiplayer game. Characters are part of a long-lived open persistent world
placed in the late middle ages, where they will usually take the role of prominent members of society (e.g. commanders, 
traders, treasurers, rulers). Cooperation among players is a core part of the game, and is required for most scenarios.

Unlike other similar games, the players do not need to log-in frequently or at certain times. Also, the level of 
deepness and involvement can be variable, and there is no benefit from spending large amounts of time playing. There is 
no fixed objective in this game, but there are many open possibilities for the players.

The in-game world is set in a fictional history after a long period of peace where a large empire controlled the whole
known world. This empire entered a decadent state and finally fell.

Players of Finem Imperii don't have any set goal. They may do as they wish and there is no way of "winning" the game.
But there are many open possibilities. A player may choose to constructively take part of a realm and help it move
forward in many different ways, or they may choose to strive to attain as much power as possible. They may also try
to work for their own personal gain, explore the world freely or engage in trade.

The different states in the fictional world are all opposed to the barbaric regions. Additionally, they may freely 
form their relationships with each other, for example by declaring war, making peace and forming alliances.

Hierarchies and political organizations are a core part of the realms in the game. And, as in the real world, a good
ruler will need to delegate it's powers to his subordinates if he want to rule efficiently. As such, trust and treason
are aspects to consider.

Players may form armies by raising local levies, training professional soldiers or hiring mercenaries. When opposing
armies meet, a battle starts.

The passing of time is turn based, and all players take their turns at the same time. A turn passes every 12 hours.
In the game world, each turn marks the pass of a month. Some actions in the game have an immediate effect, while others
happen always at the end of turn.

The game is web-based and playable with any modern browser. The main focus is on desktop computers. It should be
possible to play also on other devices, like tablets and smartphones. Simple 3D rendering of the world is a part of the
game.

# Conceptualization

This is the presentation text that is shown on the home page.

> After seven prosper centuries of peace under the rule of the Empire, it entered a stage of spiralling decadence. Not 
even the noblest rulers, the brightest bureaucrats or bravest generals were able to stop it. They were too few of them 
amongst the corrupt, the lazy and the feckless. What seemed impossible in the past, what was for many even unthinkable, 
happened in just a few decades: the Empire fell.
>
> It has now been over a hundred years of bloody civil wars, anarchy, shameless corruption and violence that has 
profoundly decimated the population. Trust in leaders became trait to be exploited. The future looked grim. But now new 
states and rulers are starting to rise again, bringing the people the hope of seeing order and peace restored.
>
> Who will be able to bring hope and dignity to the world? Will you help bringing the golden days of the Empire back?

This is a screenshot of the current "travel" page.

![Travel page screenshot](https://github.com/jardiacaj/finem_imperii/raw/master/docs/screenshot-travel-2017-03-07.png "Travel page screenshot")

# Development

Finem Imperii is web-based and oriented to modern browsers and will therefore use HTML5 and Javascript. For the 
front-end, the [boostrap][1] framework is used. The [jQuery][2] JavaScript library is used. For 3D rendering in the 
client browser, [Three.js][3] is used.

In the back-end, the [Django][4] and the Python 3 language will be used.

The rationale for these decisions is based on the following key points:
 - These are all well-known, mature tools for web development.
 - They are all open-source.
 - The developer is at least somewhat knowledgeable using those.

# Roadmap

Week    | Dates          |  Notes
------- | -------------- | -----
Week 1  | 02-27 to 03-05 |
Week 2  | 03-06 to 03-12 |
Week 3  | 03-13 to 03-19 | 03-15 is PAC1 end date
Week 4  | 03-20 to 03-26 | 50% vacation.
Week 5  | 03-27 to 04-02 |
Week 6  | 04-03 to 04-09 |
Week 7  | 04-10 to 04-16 | 25% vacation.
Week 8  | 04-17 to 04-24 | 25% vacation. 04-23 is PAC2 end date
Week 9  | 04-25 to 04-30 |
Week 10 | 05-01 to 05-07 |
Week 11 | 05-08 to 05-14 |
Week 12 | 05-15 to 05-21 | 05-20 is PAC3 end date
Week 13 | 05-22 to 05-28 | 
Week 14 | 05-29 to 06-04 | 06-04 is final delivery date

## Week 1

 - Review old code. (1 day) (finished)
 - Update dependencies. (1 hour) (finished)
 - Design draft and planning. (2 days) (finished)
 - Base tool setup. (1/2 day) (finished)
 - Character creation. (1 day) (finished)

Allocated: ~5 days

## Week 2

 - Base template. (2 hours) (finished)
 - World map rendering. (1,5 days) (finished)
 - Travelling. (1 day) (finished)
 - World population. (1/2 day) (finished)
 - Recruitment. (1,5 days)
 - Notifications. (1/2 day)
 - PAC1. (1/2 day)

Allocated: ~5 days

## Week 3

 - Messaging. (1 day)
 - Organizations. (1 day)
 - Elections. (1 day) 
 - Secession and rebellion. (1 day)

Allocated: 4 days

## Week 4

 - Conquest. (1 day)
 - CI and Dockerization (1 day)
 - Battle rework. (1 day)

Allocated: 3 days (vacation!)

## Week 5

 - Battle rendering. (1,5 days)
 - Battle orders. (2 days)
 - Sieges. (1 day)

Allocated: 4,5 days
 
## Week 6

 - Diplomacy. (1 day)
 - Barbarians. (2 days)
 - Building production (1 day)
 - Test environment setup (1/2 day)

Allocated: 4,5 days

## Week 7 

 - Trade (1,5 days)
 - Taxation (1 day)
 - PAC2 (1/2 day)
 
Allocated: 3 days (vacation!)
 
## Week 8 
 
 - Closed alpha release (1 day)
 - Game start/tutorial (2 days)

Allocated: 3 days (vacation!)

## Week 9

Buffer for unplanned issues.

## Week 10

Buffer for unplanned issues.

## Week 11
 
 - PAC3 (1/2 day)
 - Final delivery preparation
 
## Week 12

Final delivery preparation
 
## Week 13
 
Final delivery preparation
 
## Week 14

Final delivery

[1]: https://getboostrap.com
[2]: https://jquery.com
[3]: https://threejs.org
[4]: https://www.djangoproject.com
