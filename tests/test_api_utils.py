from common import ROOT, NinjabotTestCase
import os
import unittest
from unittest.mock import MagicMock


class FakeAPI(object):
    pass

APIS = {
    'fake_api': FakeAPI
}


class TestAPIUtils(NinjabotTestCase):
    def setUp(self):
        import ninjabot
        self.bot = ninjabot.Ninjabot(
            os.path.join(ROOT, '.ninjabot_config'),
            test_mode=True
        )

    def test_load_apis(self):

        self.bot.load_apis('misc.fake_api', MagicMock(APIS=APIS))
        self.assertEqual(self.bot.apis['fake_api'], FakeAPI)

    def test_request_api(self):
        import ninjabot

        self.bot.load_apis('misc.fake_api', MagicMock(APIS=APIS))

        api = self.bot.request_api('fake_api')
        self.assertEqual(api, FakeAPI)

        self.assertRaises(
            ninjabot.MissingAPIError,
            self.bot.request_api,
            ('unknown_api')
        )

        self.assertEqual(self.bot.request_api('unknown_api', False), None)


if __name__ == '__main__':
    unittest.main()
