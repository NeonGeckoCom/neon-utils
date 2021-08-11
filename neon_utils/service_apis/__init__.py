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

from threading import Event
from enum import Enum
from neon_utils import LOG
from neon_utils.configuration_utils import get_neon_auth_config, get_neon_local_config
from neon_utils.socket_utils import b64_to_dict
from neon_mq_connector.connector import MQConnector, ConsumerThread

AUTH_CONFIG = get_neon_auth_config()


class NeonAPI(Enum):
    def __str__(self):
        return self.value

    ALPHA_VANTAGE = "alpha_vantage"
    OPEN_WEATHER_MAP = "open_weather_map"
    WOLFRAM_ALPHA = "wolfram_alpha"
    FINANCIAL_MODELING_PREP = "financial_modeling_prep"
    NOT_IMPLEMENTED = "not_implemented"


class NeonAPIMQHandler(MQConnector):
    def __init__(self, config: dict, service_name: str):
        super().__init__(config, service_name)
        self.connection = self.create_mq_connection(vhost='/neon_api')


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

    response_data = dict()

    try:
        request_data = {**query_params, **{"service": str(api)}}
        LOG.debug(f'Received request data: {request_data}')
        response_event = Event()
        LOG.debug('Creating Neon API MQ Handler Instance...')
        config = get_neon_local_config().content
        LOG.info(f"MQ Config={config.get('MQ')}")
        neon_api_mq_handler = NeonAPIMQHandler(config=config, service_name='mq_handler')
        LOG.debug(f'Established MQ connection: {neon_api_mq_handler.connection}')
        if not neon_api_mq_handler.connection.is_open:
            raise ConnectionError("MQ Connection not established.")
        message_id = neon_api_mq_handler.emit_mq_message(connection=neon_api_mq_handler.connection,
                                                         queue='neon_api_input',
                                                         request_data=request_data,
                                                         exchange='')
        LOG.debug(f'Generated message id: {message_id}')

        def handle_neon_api_output(channel, method, properties, body):
            """
                Method that handles Neon API output.
                In case received output message with the desired id, event stops
            """
            api_output = b64_to_dict(body)
            LOG.debug(f'API output: {api_output}')
            api_output_msg_id = api_output.pop('message_id', None)
            if api_output_msg_id == message_id:
                response_data.update(api_output)
                channel.basic_ack(delivery_tag=method.delivery_tag)
                response_event.set()

        neon_api_mq_handler.consumers['neon_output_handler'] = ConsumerThread(connection=neon_api_mq_handler.connection,
                                                                              queue='neon_api_output',
                                                                              callback_func=handle_neon_api_output)
        neon_api_mq_handler.run_consumers(names=('neon_output_handler',))
        response_event.wait(timeout)
        neon_api_mq_handler.stop_consumers()
    except Exception as ex:
        LOG.error(f'Exception occurred while resolving Neon API: {ex}')
    finally:
        return response_data or {"status_code": 401,
                                 "content": f"Neon API failed to give a response within {timeout} seconds",
                                 "encoding": None}
