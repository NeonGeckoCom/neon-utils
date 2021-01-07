import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.web_utils import *


class MyTestCase(unittest.TestCase):
    def test_scrape_page_for_links(self):
        links = scrape_page_for_links("neon.ai")
        self.assertIsInstance(links, dict)
        self.assertIn("about us", links.keys())

        # Relative href
        self.assertEqual(links["about us"], "https://neon.ai/aboutus")

        # Absolute href
        self.assertEqual(links["get started"], "https://neon.ai/getstarted")


if __name__ == '__main__':
    unittest.main()
