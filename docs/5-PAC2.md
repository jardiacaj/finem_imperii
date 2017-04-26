2017-04-26

# PAC 2 - Partial version

In this moment, the game works only partially and is not really
playable. Here the current status is described, organized in components.

To allow for an agile progress of this project, in almost all cases a
[minimum viable product][1] is strived for. This is the reasoning
behind the lack of some apparently critical features, like e-mail
validation.

For testing purposes the user "alice" with the password "test" can be
used. This user is created automatically on database initialization.
The main advantage of using this account is that many hard to test
functionalities can be used, as it owns characters in different
positions and situations, like Kings, members of democracies,
stateless characters, etc.

## User interface design (done)

The design of the user interface is mostly done and only minor changes
are expected. I chose a dark theme which, in my opinion, is more suited
for a text-based role-playing game.

## Registration and logging in (done)

It is possible to register and log in via the user interface. It is a
minimal version that does not include some features like e-mail
address verification, changing passwords or deleting an account. These
features will be required if the game reaches a sizable number of
players.

## Character creation (80%)

The character creation process is mostly implemented. The only aspect
missing is the character profile selection, which currently does
have no effect. Furthermore, there is currently no limit on the number
of characters per user.

## Test world: Parvus (done)

A test world has been created for running both automated and manual
tests. This world is very similar to a true gaming world. Please note
that this world is not meant to be immersive. Many names are chosen
for convenience instead of for playability.

## Actual world: Emortuus (20%)

This world has been started and may be used as a prototype, but most
elements are still missing.

## Messaging and notifications (done)

Characters may send messages to others and may choose the recipients by
geographical location (characters who are physically close), by
political relationships (characters who are politically related) or to
any selection of characters in the same world.

Also, a notification system has been implemented. Currently only
travel notifications are generated.

## Recruitment (70%)

Conscripting units has been implemented. Note that each single soldier
and world inhabitant is tracked, which has many effects:
- A settlement may get empty by recruiting every inhabitant.
- Recruiting workers will decrease economic production.
- Each inhabitant can only be recruited in one unit.
- Recruiting women will reduce birth rate.

## Unit management (70%)

Management of units is mostly implemented, including renaming, changing
the unit stance and changing the battle settings and orders for the
unit.

Missing are the transfer and disband actions, as well as the unit
payment mechanism.

## Travel (done)

Travelling is fully implemented. Travelling inside a region will consume
character time but will happen instantly, travelling to a different
region will take a turn. Units in the "following" stance will follow
the character when travelling.

## Organizations (done)

The concept "organization" in the game denotes any group or position.
These are some examples:
- A state
- A position in a state, like a King, a general, a governor
- An independent organization (a traders guild, a dinasty, etc.)

## Organization capabilities (70%)

Organizations have capabilities which can apply to itself or other
organizations. A list of currently existing capaiblities:
- Banning
- Writing policy
- Conscription
- Diplomacy
- Dissolve (not implemented)
- Manage subordinate organzations (not implemented)
- Secede (not implemented)
- Manage membership (not implemented)
- Set heir (not implemented)
- Vote in elections
- Present candidacy in elections
- Convoke elections
- Set military orders
- Set military formation

## Organization elections (done)

Some positions within an organization may be elected democratically.

## Battle start (done)

An algorithm searches for potential military conflicts and starts
battles if needed. This takes into account diplomatic relationships,
military stances, unit status and existing battles.

When a battle starts (which takes one full turn) the units are split
into sub-units called [contubernia][2] and placed in formation on the
battlefield.

## Battle orders and movement (30%)

Characters can give their units orders for each round in a battle.
Units will act accordingly.

The path searching algorithm A* has been implemented, but there are
still some bugs present. Also, not every battle order is working.

# Important missing features

## Further character actions

## Barbarians

## Economy

## Battle resolution and conquest

## Help system

[1]: https://en.wikipedia.org/wiki/Minimum_viable_product
[2]: https://en.wikipedia.org/wiki/Contubernium