# NEON AI (TM) SOFTWARE, Software Development Kit & Application Development System
#
# Copyright 2008-2021 Neongecko.com Inc. | All Rights Reserved
#
# Notice of License - Duplicating this Notice of License near the start of any file containing
# a derivative of this software is a condition of license for this software.
# Friendly Licensing:
# No charge, open source royalty free use of the Neon AI software source and object is offered for
# educational users, noncommercial enthusiasts, Public Benefit Corporations (and LLCs) and
# Social Purpose Corporations (and LLCs). Developers can contact developers@neon.ai
# For commercial licensing, distribution of derivative works or redistribution please contact licenses@neon.ai
# Distributed on an "AS IS” basis without warranties or conditions of any kind, either express or implied.
# Trademarks of Neongecko: Neon AI(TM), Neon Assist (TM), Neon Communicator(TM), Klat(TM)
# Authors: Guy Daniels, Daniel McKnight, Regina Bloomstine, Elon Gasper, Richard Leeds
#
# Specialized conversational reconveyance options from Conversation Processing Intelligence Corp.
# US Patents 2008-2021: US7424516, US20140161250, US20140177813, US8638908, US8068604, US8553852, US10530923, US10530924
# China Patent: CN102017585  -  Europe Patent: EU2156652  -  Patents Pending

import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.search_utils import *


CON_DICT = {"cattalk.com,12345,Cat Talk Convo": ["cat", "talk", "convo"],
            "dogreport.com,54321,Dog Report Convo": ["dog", "report", "convo"]}

DOM_DICT = {"cattalk.com": ["cat", "cats", "cattalk", "cat talk"],
            "dogreport.com": ["dog", "dogs", "dogreport", "dog report"]}

MSG_DICT = {"cattalk.com,12345,0,username,sid,how are you doing": ["how", "are", "you", "doing"],
            "dogreport.com,54321,0,username,sid,I love my dog": ["i", "love", "my", "dog"]}


class SearchUtilTests(unittest.TestCase):
    def test_search_con(self):
        results = search_convo_dict(CON_DICT, "cat")
        self.assertIn("cattalk.com,12345,Cat Talk Convo", results)

        results = search_convo_dict(CON_DICT, "convo")
        self.assertIn("cattalk.com,12345,Cat Talk Convo", results)
        self.assertIn("dogreport.com,54321,Dog Report Convo", results)

    def test_search_dom(self):
        results = search_convo_dict(DOM_DICT, "cat")
        self.assertIn("cattalk.com", results)
        self.assertNotIn("dogreport.com", results)

    def test_search_shout(self):
        results = search_convo_dict(MSG_DICT, "dog")
        self.assertIn("dogreport.com,54321,0,username,sid,I love my dog", results)

    # # TODO: Need to document typo handling/search expected results DM
    # def test_search_typo(self):
    #     results = search_convo_dict(MSG_DICT, "dig", handle_typos=True)
    #     self.assertIn("dogreport.com,54321,0,username,sid,I love my dog", results)
    #
    #     results = search_convo_dict(MSG_DICT, "dig", handle_typos=False)
    #     self.assertNotIn("dogreport.com,54321,0,username,sid,I love my dog", results)


if __name__ == '__main__':
    unittest.main()
