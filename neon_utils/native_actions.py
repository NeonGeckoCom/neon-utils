# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2026 Neongecko.com Inc.
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

import time
"""
Shared helper for Node native actions (`node.invoke_native`).

A skill that calls `invoke_native_action` must ship these dialog files:

- `native_action_not_supported.dialog`
- `native_action_success.dialog` (spoken only when `confirm_on_success` is set)
- `native_action_timeout.dialog`
- `native_action_error.dialog`
- one `<NodeNativeAction value>.dialog` per action the skill invokes, e.g.
  `launch_camera_app.dialog`, holding the spoken name of that action

Every `native_action_*` dialog receives `{action}` and `{description}`;
`native_action_error` also receives `{code}` and `{message}`. A missing
dialog file gets the standard OVOS behavior: the key itself is spoken.
"""

import threading

from dataclasses import dataclass
from enum import Enum
from typing import Optional, TYPE_CHECKING

from ovos_bus_client import Message
from ovos_utils.log import LOG

from neon_data_models.enum import NodeNativeAction, NativeActionErrorCode

if TYPE_CHECKING:
    from neon_utils.skills.neon_skill import NeonSkill

INVOKE_TYPE = "node.invoke_native"
RESPONSE_TYPE = "node.invoke_native.response"

# Default response timeout in seconds, per action.
_DEFAULT_TIMEOUTS = {
    NodeNativeAction.LAUNCH_CAMERA_APP.value: 10,
    NodeNativeAction.LAUNCH_VOICE_RECORDER_APP.value: 10,
    NodeNativeAction.LAUNCH_REMINDERS_APP.value: 5,
    NodeNativeAction.LAUNCH_CLOCK_APP.value: 5,
    NodeNativeAction.LAUNCH_SMS_APP.value: 5,
    NodeNativeAction.LAUNCH_EMAIL_APP.value: 5,
}
_FALLBACK_TIMEOUT = 5


class NativeActionOutcome(Enum):
    SUCCESS = "success"
    NOT_SUPPORTED = "not_supported"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class NativeActionResult:
    outcome: NativeActionOutcome
    error_code: Optional[NativeActionErrorCode] = None
    error_message: str = ""


def invoke_native_action(skill: "NeonSkill", message: Message,
                         action: NodeNativeAction,
                         params: Optional[dict] = None) -> NativeActionResult:
    """
    Capability-gate, dispatch, and await a `node.invoke_native` request.
    Shared by every skill's `if node:` branch so the flow (gate, emit,
    await, settings) lives in one place.
    :param skill: the calling NeonSkill instance (its `speak_dialog` must
        accept `message=`, which the OVOSSkill base does not)
    :param message: the triggering Message (must carry `context.node`)
    :param action: `NodeNativeAction` to invoke
    :param params: optional payload (only meaningful for sms/email actions)
    :returns: `NativeActionResult` describing what happened
    """
    action_value = action.value if isinstance(action, NodeNativeAction) \
        else action
    node_ctx = message.context.get("node") or {}
    capabilities = node_ctx.get("capabilities") or {}

    if not capabilities.get(action_value):
        LOG.debug(f"Node does not support {action_value}; "
                  f"capabilities={capabilities}")
        _speak_not_supported(skill, message, action_value)
        return NativeActionResult(NativeActionOutcome.NOT_SUPPORTED)

    session_id = _session_of(message) or node_ctx.get("node_id")

    invoke_msg = message.reply(INVOKE_TYPE,
                               {"action": action_value,
                                "params": params or {}})
    waiter = _ResponseWaiter(skill.bus, session_id, action_value)
    skill.bus.emit(invoke_msg)
    response = waiter.wait(_resolve_timeout(skill, action_value))

    if response is None:
        LOG.warning(f"Timed out awaiting {RESPONSE_TYPE} for "
                    f"action={action_value} session={session_id}")
        _speak_timeout(skill, message, action_value)
        return NativeActionResult(NativeActionOutcome.TIMEOUT)

    return _interpret_response(skill, message, action_value, response)


class _ResponseWaiter:
    """
    Subscribes before the request is emitted, so a reply that lands before
    `emit()` returns is still caught. Filters on action and session so
    concurrent requests on a shared bus cannot take each other's reply.
    """

    def __init__(self, bus, session_id: Optional[str], action_value: str):
        self._bus = bus
        self._session_id = session_id
        self._action_value = action_value
        self._received = threading.Event()
        self._handler = self._on_response
        self.response: Optional[Message] = None
        bus.on(RESPONSE_TYPE, self._handler)

    def wait(self, timeout: float) -> Optional[Message]:
        try:
            self._received.wait(timeout)
        finally:
            self._bus.remove(RESPONSE_TYPE, self._handler)
        return self.response

    def _on_response(self, response: Message):
        if not self._matches(response):
            LOG.debug(f"Ignoring {RESPONSE_TYPE} for "
                      f"action={response.data.get('action')} "
                      f"session={_session_of(response)}")
            return
        self.response = response
        self._received.set()

    def _matches(self, response: Message) -> bool:
        if response.data.get("action") != self._action_value:
            return False
        return self._session_id is None or \
            _session_of(response) == self._session_id


def _session_of(message: Message) -> Optional[str]:
    return message.context.get("session", {}).get("session_id")


def _interpret_response(skill: "NeonSkill", message: Message,
                        action_value: str,
                        response: Message) -> NativeActionResult:
    if response.data.get("status") == "success":
        if skill.settings.get("confirm_on_success", False):
            _speak_success(skill, message, action_value)
        return NativeActionResult(NativeActionOutcome.SUCCESS)

    error = response.data.get("error") or {}
    try:
        error_code = NativeActionErrorCode(error.get("code"))
    except ValueError:
        error_code = NativeActionErrorCode.INTERNAL_ERROR
    error_message = error.get("message", "")
    _speak_error(skill, message, action_value, error_code, error_message)
    return NativeActionResult(NativeActionOutcome.ERROR, error_code,
                              error_message)


def _resolve_timeout(skill: "NeonSkill", action_value: str) -> float:
    overrides = skill.settings.get("per_action_timeouts") or {}
    if action_value in overrides:
        try:
            return float(overrides[action_value])
        except (TypeError, ValueError):
            LOG.warning(f"Invalid per_action_timeouts override for "
                        f"{action_value}: {overrides[action_value]!r}")
    return _DEFAULT_TIMEOUTS.get(action_value, _FALLBACK_TIMEOUT)


def _speak_not_supported(skill: "NeonSkill", message: Message,
                         action_value: str):
    skill.speak_dialog("native_action_not_supported",
                       _dialog_data(skill, action_value), message=message)


def _speak_success(skill: "NeonSkill", message: Message, action_value: str):
    skill.speak_dialog("native_action_success",
                       _dialog_data(skill, action_value), message=message)


def _speak_timeout(skill: "NeonSkill", message: Message, action_value: str):
    skill.speak_dialog("native_action_timeout",
                       _dialog_data(skill, action_value), message=message)


def _speak_error(skill: "NeonSkill", message: Message, action_value: str,
                 error_code: NativeActionErrorCode, error_message: str):
    skill.speak_dialog("native_action_error",
                       _dialog_data(skill, action_value,
                                    code=error_code.value,
                                    message=error_message),
                       message=message)


def _dialog_data(skill: "NeonSkill", action_value: str, **extra) -> dict:
    return {"action": action_value,
            "description": _describe(skill, action_value), **extra}


def _describe(skill: "NeonSkill", action_value: str) -> str:
    """Render `<action_value>.dialog`; the raw key if the file is missing."""
    renderer = skill.dialog_renderer
    if not renderer:
        LOG.warning(f"No dialog_renderer; speaking raw key {action_value}")
        return action_value
    return renderer.render(action_value)
