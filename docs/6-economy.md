# Economy v1

## Money

* Fixed monetary mass
* Organizations may own treasury building.

### Salaries and taxes

* Character may get salary from organization
* NPCs get unit salary from owner (10c/mo)

### Start money

* NPC: 50 coins
* Start realm: 20


## Food

See 3-buildings.md

NPCs may earn money by selling food they produced.

### Food consumption

* NPCs eat 1 ration/mo
* NPC has hunger counter which starts at -9
* Negative health effects start to happen at hc > 0
* Negative hunger counter means NPC has stored food

### Food spoilage

* Every month food is spoiled by multiplying by 0.9889
* Goal: default food surplus of 20% spoils to a surplus of 5% at the
end of the year.

### Food market

NPCs will start trying to buy food from the market when their hunger
counter rises.

| Hunger level | Action |
| --- | --- |
| <= -11 | sells at 4 coins or 4% of cash, whichever is more |
| <= -10 | sells at 5 coins or 4% of cash, whichever is more |
| <= -9 | sells at 6 coins or 4% of cash, whichever is more |
| -8 to -3 | no action |
| -2 | buy at 5 coins or 4% of cash, whichever is higher, up to 50 coins |
| -1 | buy at 5 coins or 8% of cash, whichever is higher, up to 100 coins |
| 0 | buy at 5 coins or 25% of cash, whichever is higher, up to 250 coins |
| 1 | buy at 50% of cash, up to 500 coins |
| 2 | buy at any price |

Market works by: iterate buyers (hc >= -2) in a random order. First gets
to pick the lowest seller and buy at that price.

Characters may spend time to find buyers or sellers.

## NPC jobs

See 3-buildings.md

NPCs are assigned to jobs at buildings. Unemployed NPCs will search a
job at each turn. NPCs may be forced to change jobs, for example when
they are recruited or selected to run some building.
