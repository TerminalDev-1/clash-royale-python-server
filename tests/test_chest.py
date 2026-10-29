import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'server'))
import test_server as server

class ChestTest(unittest.TestCase):
    def test_reward_persists_and_cooldown_prevents_double_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(server, 'STATE_PATH', Path(directory) / 'player.json'):
                state = server.load_state()
                self.assertTrue(server.collect_free_chest(state, 1000))
                self.assertEqual((state['gold'], state['gems'], state['card_count']), (1050, 102, 3))
                self.assertFalse(server.collect_free_chest(state, 1001))
                self.assertEqual(server.load_state(), state)
                self.assertTrue(server.collect_free_chest(state, 15400))
                self.assertEqual((state['gold'], state['gems'], state['card_count']), (1100, 104, 6))

if __name__ == '__main__':
    unittest.main()
