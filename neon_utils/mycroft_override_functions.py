import time

from mycroft_bus_client import Message

from neon_utils.logger import LOG


def speak(utterance, expect_response=False, message=None, private=False, speaker=None, wait=False, meta=None):
    """
    Speak a sentence.
    Arguments:
        utterance (str):        sentence mycroft should speak
        expect_response (bool): set to True if Mycroft should listen for a response immediately after
                                speaking the utterance.
        message (Message):      message associated with the input that this speak is associated with
        private (bool):         flag to indicate this message contains data that is private to the requesting user
        speaker (dict):         dict containing language or voice data to override user preference values
        wait (bool):            set to True to block while the text is being spoken.
        meta:                   Information of what built the sentence.
    """
    from neon_utils import SKILL

    # registers the skill as being active
    meta = meta or {}
    meta['skill'] = SKILL.name
    SKILL.enclosure.register(SKILL.name)
    if utterance:
        LOG.debug(f">>>>> Skill speak! {utterance}")
        # check_for_signal("CORE_andCase")
        # print("Hey")
        # print(message.data) This may not be defined here!

        # Find the associated message
        if message:
            LOG.info('message passed to speak = ' + str(message.data))
            if not speaker:
                speaker = message.data.get("speaker", None)
        else:
            LOG.debug('message is None.')
            message = dig_for_message()

        if message:
            # filename = message.context.get("flac_filename", "")
            # cc_data = message.context.get("cc_data", {})
            # profiles = message.context.get("nick_profiles", {})
            if not speaker:
                speaker = message.data.get("speaker", speaker)
            # if message.data['flac_filename']:
            #     filename = message.data['flac_filename']
            # else:
            #     filename = ''
        else:
            message = dig_for_message()
            filename = ''
            # cc_data = {}
            # profiles = {}
            if message:
                # filename = message.context.get("flac_filename", "")
                # cc_data = message.context.get("cc_data", {})
                # profiles = message.context.get("nick_profiles", {})
                if not speaker:
                    speaker = message.data.get("speaker", {})

        # registers the skill as being active
        # print(f'{cc_data} is cc_data')
        # self.enclosure.register(self.name)
        nick = ""
        # LOG.debug(nick)
        data = {"utterance": utterance,
                "expect_response": expect_response,
                "meta": meta,
                # "flac_filename": filename,
                # "cc_data": cc_data,
                # "private": private,
                # "nick": nick,
                # "nick_profiles": profiles,
                "speaker": speaker}

        # devices might not want to do these logs either... weird characters cause a logging error
        if not SKILL.server:
            LOG.info(f'{speaker} Speak: {utterance}')
            # LOG.info('Speak data = ' + str(data))
        # LOG.info(filename)
        if not message:
            message = dig_for_message()

        if message and message.context.get("cc_data", {}).get("emit_response"):
            LOG.debug(f"DM: {data}")
            msg_to_emit = message.reply("skills:execute.response", data)

        elif message and message.msg_type != "mycroft.ready":
            message.context.get("timing", {})["speech_start"] = time.time()
            LOG.info("message True, " + str(data))
            # LOG.info(message)
            # TODO: This is where we have the most complete timing profile for an utterance
            # LOG.debug(f"TIME: to_speak, {time.time()}, {message.context['flac_filename']}, {data['utterance']}, "
            #           f"{message.context}")
            # self.bus.emit(message.reply("speak", data))
            msg_to_emit = message.reply("speak", data)
            LOG.debug(f">>>> Skill speak! {data}, {message.context}")
        else:
            LOG.warning("message False, " + str(data))
            # self.bus.emit(Message("speak", data))
            msg_to_emit = Message("speak", data)
        LOG.debug(msg_to_emit.msg_type)
        SKILL.bus.emit(msg_to_emit)
    else:
        LOG.warning("Null utterance passed to speak")
        LOG.warning(f"{SKILL.name} | message={message}")

    if wait:
        wait_while_speaking()


def dig_for_message():
    """Dig Through the stack for message."""
    import inspect

    stack = inspect.stack()
    # Limit search to 10 frames back
    stack = stack if len(stack) < 10 else stack[:10]
    local_vars = [frame[0].f_locals for frame in stack]
    for var in local_vars:
        if 'message' in var and isinstance(var['message'], Message):
            return var['message']


def wait_while_speaking():
    """Pause as long as Text to Speech is still happening

    Pause while Text to Speech is still happening.  This always pauses
    briefly to ensure that any preceding request to speak has time to
    begin.
    """
    LOG.debug("Wait while speaking!")
    time.sleep(0.3)  # Wait briefly in for any queued speech to begin
    while is_speaking():
        time.sleep(0.1)


def is_speaking():
    """Determine if Text to Speech is occurring

    Returns:
        bool: True while still speaking
    """
    from neon_utils.skill_override_functions import check_for_signal
    return check_for_signal("isSpeaking", -1)
