ninjabot-misc
=============

A motley collection of miscelaneous plugins for ninjabot.

regex.py
--------

Regex replace plugin for ninjabot.
Watches incoming messages for sed substitution strings.
Supports using any-character separator if `<prefix>sed` is used.

###Config

```
"misc.regex": {
	"backlog": (int) /* Number of messages to retain for each user. Defaults to 5. */
}
```
