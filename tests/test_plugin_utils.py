from common import ROOT, NinjabotTestCase

import os
import unittest
from unittest.mock import MagicMock, patch


class FakePlugin(object):
    """
    A fake plugin that exposes dummy methods to test Ninjabot methods
    """
    def on_incoming(self):
        pass

    def trigger_world(self):
        pass

    def timer_10(self):
        pass


class TestPluginUtils(NinjabotTestCase):
    def setUp(self):
        import ninjabot

        self.bot = ninjabot.Ninjabot(
            os.path.join(ROOT, '.ninjabot_config'),
            test_mode=True
        )
        self.bot.logger = MagicMock()

    def test_load_plugins(self):
        # not worth testing this, all it does is call other functions
        pass

    @patch('ninjabot.Ninjabot.register_inbuilt_triggers')
    def test_clear_plugin_data(self, _):
        self.bot.clear_plugin_data()

        self.assertEqual(self.bot.plugins, {})
        self.assertEqual(self.bot.incoming, [])

        self.assertEqual(self.bot.timers, [])
        self.assertEqual(self.bot.storage, [])
        self.assertEqual(self.bot.apis, {})

    def test_register_inbuilt_triggers(self):
        self.bot.register_inbuilt_triggers()
        self.assertTrue(
            {'reload', 'kill', 'restart'}.issubset(self.bot.triggers.keys())
        )

    def recurse_plugin_config(self):
        pass

    # i don't appear to understand how the load function is supposed
    # to work, i cant write this test - Dom/Lord_DeathMatch/Mause
    # @patch('ninjabot.Ninjabot.load')
    # def test_load_all_from_path(self, load):
    #     import tempfile
    #     path = tempfile.mkdtemp()
    #     import pudb
    #     pu.db
    #     fd, filename = tempfile.mkstemp('.py', dir=path)

    #     path = os.path.relpath(path)

    #     self.bot.load_all_from_path(path + '/')
    #     load.assert_called_with(filename[:-3])

    @patch('imp.reload')
    @patch('ninjabot.import_module')
    @patch('ninjabot.Ninjabot.load_plugin')
    @patch('ninjabot.Ninjabot.load_apis')
    def test_load(self, load_plugin, load_apis, import_module, reload):
        reload.return_value = MagicMock()
        self.bot.load('this_is_path')

        import_module.assert_called_with('this_is_path')
        load_apis.assert_called_with('this_is_path', reload.return_value)
        load_plugin.assert_called_with('this_is_path', reload.return_value)

    @patch('imp.reload')
    @patch('ninjabot.import_module')
    @patch('ninjabot.Ninjabot.report_error')
    def test_load_failure(self, report_error, import_module, reload):
        reload.side_effect = Exception

        self.bot.load('this_is_path')

        import_module.assert_called_with('this_is_path')
        report_error.assert_called_with()

    def test_load_plugin(self):
        module = MagicMock(name='random_module', Plugin=FakePlugin)

        self.bot.load_plugin('plugins.misc.random_module', module)
        instantiated_plugin = self.bot.plugins['misc.random_module']

        self.assertIsInstance(instantiated_plugin, FakePlugin)
        self.assertEqual(self.bot.plugins['misc.random_module'], instantiated_plugin)
        self.assertIn(instantiated_plugin.on_incoming, self.bot.incoming)
        self.assertEqual(self.bot.triggers.get('world'), instantiated_plugin.trigger_world)

        # one is from FakePlugin, the other is builtin
        self.assertGreaterEqual(len(self.bot.timers), 1)

    def test_initiate_plugins(self):
        plugin = MagicMock()
        config = {'config': 'config'}

        self.bot.plugins = {'fake_plugin': plugin}
        self.bot.config = {'fake_plugin': config}

        self.bot.initiate_plugins()
        plugin.load.assert_called_with(self.bot, config)


if __name__ == '__main__':
    unittest.main()
