import unittest
from golos import Api


class GolosTestCase(unittest.TestCase):
    def setUp(self):
        self.golos = Api()


if __name__ == "__main__":
    unittest.main()
