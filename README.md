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
have an API key for a particular service, it is recommended you disable the plugin.
The config file contains instructions on how to enable and disable plugins

Plugins
-------

ninjabot comes with a core set of plugins which provide enough functionality to manage the
bot, and not much else. Additional plugins can be obtained from the following repositories:

* [ninjabot-games](https://github.com/ackwell/ninjabot-games)
* [ninjabot-misc](https://github.com/ackwell/ninjabot-misc)

To include any of these, navigate to the `plugins/` folder and `git clone` them in. Make
sure to enable them in your config!

Of course, feel free to write your own, that's the true power of this bot. If you write a plugin
that you think would benefit the core codebase or any of the additional plugin repos, by all means,
send a pull request! Additions are always welcome.

Writing Plugins
---------------

To get started writing plugins, check `plugins/example.py`, it shows the general structure
of a plugin, and contains a quickstart on the more common bot commands. (It's a bit outdated,
but still relevant. I should update that...). For further info, the best thing to do it to take
a look through the main bot code. A plugin can leverage any functionality that can be accessed
through the Ninjabot class (passed to plugins as `bot`).

Good examples of working plugins are floating around. I'd suggest taking a look at the 'Uno'
plugin in ninjabot-games, as it's quite large, with it's own help system and the like.

Happy botting!
