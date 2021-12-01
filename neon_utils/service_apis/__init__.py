# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from enum import Enum
from neon_utils.configuration_utils import get_neon_auth_config
from neon_utils.mq_utils import send_mq_request

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
    response = send_mq_request("/neon_api", request_data, "neon_api_input", "neon_api_output", timeout)
    return response or {"status_code": 401,
                        "content": f"Neon API failed to give a response within {timeout} seconds",
                        "encoding": None}
