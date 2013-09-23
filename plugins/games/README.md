ninjabot-games
==============

A collection of IRC game plugins for ninjabot.

uno.py
------

Port of the card game UNO!, for IRC. Because its fun, and why not. All the commands used to
play are sub-commands of `<prefix>uno`

###Config:

```
"games.uno": {
	"join_phase": (float), /* Time (in minutes) the join phase lasts for. Defaults to 2. */
	"cooldown": (float), /* Time (in minutes) the game cooldown lasts for. Defaults to 10.*/
	"announce_cooldown": (boolean) /* Whether or not the bot should announce when cooldown is over. Defaults to true. */
}
```
