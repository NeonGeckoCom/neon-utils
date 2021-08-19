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

from enum import Enum
from neon_utils.configuration_utils import get_neon_auth_config
from neon_utils.mq_utils import get_mq_response

AUTH_CONFIG = get_neon_auth_config()


class NeonAPI(Enum):
    def __str__(self):
        return self.value

    ALPHA_VANTAGE = "alpha_vantage"
    OPEN_WEATHER_MAP = "open_weather_map"
    WOLFRAM_ALPHA = "wolfram_alpha"
    FINANCIAL_MODELING_PREP = "financial_modeling_prep"
    NOT_IMPLEMENTED = "not_implemented"
    TEST_API = "api_test_endpoint"


def request_neon_api(api: NeonAPI, query_params: dict, timeout: int = 30) -> dict:
    """
        Handle a request for information from the Neon API Proxy Server
        :param api: Service API to target
        :param query_params: Data parameters to pass to service API
        :param timeout: Request timeout in seconds
        :return: dict response from API with: `status_code`, `content`, and `encoding`
    """

    if not isinstance(api, NeonAPI):
        raise TypeError(f"Expected a NeonAPI, got: {api}")
    if not query_params:
        raise ValueError("Got empty query params")
    if not isinstance(query_params, dict):
        raise TypeError(f"Expected dict, got: {query_params}")

    request_data = {**query_params, **{"service": str(api)}}
    response = get_mq_response("/neon_api", request_data, "neon_api_input", "neon_api_output", timeout)
    return response or {"status_code": 401,
                        "content": f"Neon API failed to give a response within {timeout} seconds",
                        "encoding": None}
