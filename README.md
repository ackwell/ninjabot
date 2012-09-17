ninjabot
========

**n**injabot **i**s **n**ot **j**ust **a**nother **bot**: An extensible Python IRC bot

Setting up
----------

Setup for ninjabot is pretty simple. Clone the repo, then copy the config file to your home
directory.

    $ git clone https://github.com/ackwell/ninjabot.git
    $ cd ninjabot
    $ cp .ninjabot_config ~

You will then want to edit the config file with your details and API keys. If you don't
have an API key for a particular service, it is reccomended you disable the plugin.
Plugins can be disabled by (as outlined in `Plugins/example.py`) adding `active = False`
as a class variable.

Plugins
-------

ninjabot comes with an (ever expanding) base set of plugins which should be more than
enough to get you started, but the true power of the bot comes when you make your own.

To get started writing plugins, check `Plugins/example.py`, it shows the general structure
of a plugin, and contains a quickstart on the more common controller functions. For further
info, the best thing to do is to take a look though the main bot code, a plugin is able to 
leverage any functionality that can be accessed through the controller class.

For further examples, it is probably worth taking a look through the plugins included
with the bot. `Plugins/regex.py` is a good example of how to use the on_incoming hook.
`Plugins/uno.py` is an example of a large-scale plugin with it's own help system, etc.

If you write a plugin which you think would benefit the main code base, by all means, send
a pull request! Additions are always welcome.
