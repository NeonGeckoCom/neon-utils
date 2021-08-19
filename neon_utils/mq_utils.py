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
from time import sleep

from pika.exceptions import ProbableAccessDeniedError

from neon_utils import LOG
from neon_utils.socket_utils import b64_to_dict
from neon_mq_connector.connector import MQConnector, ConsumerThread
from neon_utils.configuration_utils import get_neon_local_config


class NeonMQHandler(MQConnector):
    def __init__(self, config: dict, service_name: str, vhost: str):
        super().__init__(config, service_name)
        self.vhost = vhost
        self.connection = self.create_mq_connection(vhost=vhost)

    def run_consumers(self):
        super(NeonMQHandler, self).run_consumers(names=('neon_output_handler',), daemon=True)
        self.consumers['neon_output_handler']._started.wait()
        # TODO: Waiting for consumers should be handled in NeonMQHandler DM


def get_mq_response(vhost: str, request_data: dict, target_queue: str, response_queue: str, timeout: int = 30) -> dict:
    """
    Sends a request to the MQ server and returns the response.
    :param vhost: vhost to target
    :param request_data: data to post to target_queue
    :param target_queue: queue to post request to
    :param response_queue: queue to monitor for a response
    :param timeout: time in seconds to wait for a response before timing out
    :return: response to request
    """
    response_event = Event()
    emit_event = Event()
    message_id = None
    response_data = dict()
    config = dict()

    def handle_mq_response(channel, method, _, body):
        """
            Method that handles Neon API output.
            In case received output message with the desired id, event stops
        """
        api_output = b64_to_dict(body)
        api_output_msg_id = api_output.pop('message_id', None)
        emit_event.wait(timeout)
        if not emit_event.is_set():
            LOG.error(f"Error occurred emitting request: {request_data}")
            LOG.warning(f"Ignoring response to message_id: {api_output_msg_id}")
        if api_output_msg_id == message_id:
            LOG.debug(f'MQ output: {api_output}')
            try:
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                LOG.error(e)
            response_data.update(api_output)
            response_event.set()

    try:
        # LOG.debug('Creating Neon MQ Handler Instance...')
        config = get_neon_local_config().content.get('MQ')
        # LOG.info(f"MQ Config={config}")
        neon_api_mq_handler = NeonMQHandler(config=config, service_name='mq_handler', vhost=vhost)
        # LOG.debug(f'Established MQ connection: {neon_api_mq_handler.connection}')
        if not neon_api_mq_handler.connection.is_open:
            raise ConnectionError("MQ Connection not established.")

        neon_api_mq_handler.register_consumer('neon_output_handler',
                                              neon_api_mq_handler.vhost, response_queue, handle_mq_response)
        neon_api_mq_handler.run_consumers()
        message_id = neon_api_mq_handler.emit_mq_message(connection=neon_api_mq_handler.connection,
                                                         queue=target_queue,
                                                         request_data=request_data,
                                                         exchange='')
        LOG.debug(f'Sent request: {request_data}')
        emit_event.set()
        response_event.wait(timeout)
        if not response_event.is_set():
            LOG.error(f"Timeout waiting for response on: {response_queue}")
        neon_api_mq_handler.stop_consumers()
    except ProbableAccessDeniedError:
        raise ValueError(f"{vhost} is not a valid endpoint for {config.get('users').get('mq_handler').get('user')}")
    except Exception as ex:
        LOG.error(f'Exception occurred while resolving Neon API: {ex}')
    return response_data
