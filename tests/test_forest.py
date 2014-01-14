# Standard Library
import unittest

#
from ..forest import Forest


class TestForest(unittest.TestCase):
    def setUp(self):
        self.forest = Forest()

    def test_quiet_forest(self):
        self.forest.p_lightning = 0
        self.forest.start_fires()
        self.assertEqual(self.forest.forest_fires.sum(), 0)


if __name__ == '__main__':
    unittest.main()
