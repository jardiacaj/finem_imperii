2017-05-21

# PAC 3 - Playable version

In this moment, the core aspects of the game work fully and is playable
in its current form, although not all aspects of the original design
are implemented as first conceived.

A first early access release is planned to happen soon under the URL
[fi.joanardiaca.net][1].

In this document I present first the aspects where few or no changes
have happened since the PAC2. Later on I present the aspects where
majors progress happened.

PAC2 video: https://www.youtube.com/watch?v=5st9PQ-c4mY

PAC3 video: https://www.youtube.com/watch?v=F-trGMinLgA

# Review of aspects with minor or no changes

 - User interface design (done): the interface has only minor
 improvements on the navigation bars.
 - Registration and logging in (done): no changes.
 - Test world Parvus (done): changes have been made to keep the world
 up to date and make new scenarios testable.
 - Recruitment, conscription only (done): some options have been removed
 and only conscription is implemented. Professional units and
 mercenaries have been left out.
 - Travel (done): some minor changes have been introduced, like
 restrictions on travel during battles.
 - Organizations (done): although many related features and changes
 have been implemented, no change has been done on the core concept
 of organizations.
 - Organization elections (done): only change is that elections are
 now triggered automatically when a position becomes vacant.

# Aspects with significant progress

## Character creation (done)

The major change is the introduction of character profiles. There are
now three distinct profiles. I reproduce here the text from the
character creation page:

 - The main function of commanders is to recruit and lead units to fight
 barbarians and other enemy realms. A commander can hold more units and
 soldiers and has advantages when managing units.
 - Traders move goods from one place to another, taking care of the
 logistics of realms. Traders start with transport carts, which allow
 them to carry more goods around.
 - Bureaucrats help in the organization of realms and keep their
 backbones functioning properly.

The trader and bureaucrat profiles are in an immature state. The
bureaucrat profile has no special capabilities and is not really
in a playable state. Traders only have a partial implementation but
are payable and useful in-game.

## Actual world: Emortuus (50%)

This world is not fully populated. The peninsula in the north is fully
functional and playable, but the rest of the world is empty. This is
not a problem to playability other than aesthetic.

## Messaging and notifications (done)

No changes on the messaging system have been made except for a code
refactor.

Multiple automatic notifications have been added, including
notifications related to conquests, turn passes, battles,
elections, diplomacy, etc. Most (if not all) needed notifications
in the game are now active.

## Unit management (done)

While the unit recruitment has been simplified, in the management side
the battle settings have been refined and the disband action has been
introduced.

Also, now units have to receive payment each turn. This happens
automatically. If the character does not have enough money, the
unit demobilizes and refuses to mobilize again until the character
has enough money.

## Organization capabilities (done)

The remaining needed capabilities have been implemented:

- Conquest
- Manage taxes
- Manage guilds
- Take grain

Some obsolete capabilities have been removed, like dissolving,
seceding, managing memberships, etc.

## Battle start (done)

The battle start process is now fully implemented. A new major aspect
is the joining of allies on the same side of a battle. Previously,
only one state could fight another, but allies could not participate
together.

## Battle orders and movement (done)

The basic orders have been implemented: advancing in formation,
charging, fleeing and standing ground. As ranged units have not been
implemented, the range attack order has been removed.

## Battle resolution

Battles now end once one side of the conflict is either completely
defeated or leaves the battleground.

## Conquest

Conquest of regions is now possible. The owner of the conquest
capability of a state is able to start and stop conquests, while
any unit may contribute or oppose the conquest process.

## Barbarians

Barbarians units are automatically created from local population in
settlements when there are no units to ensure public order in a
settlement. This makes controlling a realm more challenging for the
players and also adds difficulty to conquering barbarian regions.

## Economy

A basic economic system has been implemented that revolves around two
resources: grain and money. Able inhabitants of the controlled
regions can work either on the fields, thus producing grain, or in
a guild, producing money. Harvesting of fields happens during the
summer months, so care has to be taken on managing the existing grain.
Also, some regions may produce a surplus, while others may need imports.
Characters can transport grain from one settlement to the other.

Inhabitants working in guilds produce money, which is collected yearly
in the form of taxes. This money can be then spent on military units.

## Help system

A lightweight help system has been introduced. It has only little
content at the current stage. The main feature is a short introduction
to the game which is also shown before players create a character.

[1]: http://fi.joanardiaca.net
