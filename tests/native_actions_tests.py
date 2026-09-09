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

import sys
import os
import threading
import time
import unittest

from unittest.mock import Mock, patch
from ovos_bus_client import Message
from ovos_utils.dialog import MustacheDialogRenderer
from ovos_utils.fakebus import FakeBus

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from neon_utils.native_actions import (invoke_native_action,
                                       NativeActionOutcome,
                                       INVOKE_TYPE, RESPONSE_TYPE,
                                       _resolve_timeout)
from neon_data_models.enum import NodeNativeAction, NativeActionErrorCode

QUICK_TIMEOUTS = {"per_action_timeouts": {"launch_camera_app": 0.2,
                                          "launch_sms_app": 0.2}}
ACTION_DIALOGS = {"launch_camera_app": ["the camera app"],
                  "launch_sms_app": ["the messages app"]}


def _node_message(action_supported: bool = True, action="launch_camera_app",
                  session_id="node-abc123"):
    context = {
        "node": {
            "node_id": "node-abc123",
            "node_name": "Kitchen Phone",
            "capabilities": {action: action_supported}
        },
        "session": {"session_id": session_id}
    }
    return Message("recognizer_loop:utterance", {}, context)


def _response(action="launch_camera_app", status="success", error=None,
              session_id="node-abc123"):
    data = {"action": action, "status": status}
    if error:
        data["error"] = error
    return Message(RESPONSE_TYPE, data, {"session": {"session_id": session_id}})


def _renderer(templates: dict) -> MustacheDialogRenderer:
    renderer = MustacheDialogRenderer()
    renderer.templates = templates
    return renderer


def _make_skill(settings=None, responses=()):
    """
    Each response is emitted synchronously from inside the invoke emit, so
    it lands before `emit()` returns. A helper that subscribed only after
    emitting would miss every one of them.
    """
    skill = Mock()
    skill.settings = settings or {}
    skill.bus = FakeBus()
    skill.dialog_renderer = _renderer(dict(ACTION_DIALOGS))
    if responses:
        skill.bus.on(INVOKE_TYPE,
                     lambda _: [skill.bus.emit(r) for r in responses])
    return skill


def _capture_invokes(skill) -> list:
    invokes = []
    skill.bus.on(INVOKE_TYPE, invokes.append)
    return invokes


def _spoken(skill):
    """(dialog key, data) of the single speak_dialog call."""
    skill.speak_dialog.assert_called_once()
    key, data = skill.speak_dialog.call_args[0]
    return key, data


class NativeActionsTests(unittest.TestCase):
    def test_not_supported_speaks_and_emits_nothing(self):
        skill = _make_skill()
        invokes = _capture_invokes(skill)
        message = _node_message(action_supported=False)

        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.outcome, NativeActionOutcome.NOT_SUPPORTED)
        self.assertEqual(invokes, [])
        key, data = _spoken(skill)
        self.assertEqual(key, "native_action_not_supported")
        self.assertEqual(data, {"action": "launch_camera_app",
                                "description": "the camera app"})

    def test_capabilities_entirely_absent_treated_as_not_supported(self):
        skill = _make_skill()
        invokes = _capture_invokes(skill)
        message = Message("recognizer_loop:utterance", {},
                          {"node": {"node_id": "node-abc123"},
                           "session": {"session_id": "node-abc123"}})

        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.outcome, NativeActionOutcome.NOT_SUPPORTED)
        self.assertEqual(invokes, [])

    def test_absent_capability_key_treated_as_not_supported(self):
        skill = _make_skill()
        invokes = _capture_invokes(skill)
        message = _node_message(action_supported=True,
                                action="launch_sms_app")
        # Request an action that has no key in capabilities at all
        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.outcome, NativeActionOutcome.NOT_SUPPORTED)
        self.assertEqual(invokes, [])

    def test_supported_emits_invoke_native_with_action_and_params(self):
        skill = _make_skill(responses=[_response(status="success")])
        invokes = _capture_invokes(skill)
        message = _node_message(action_supported=True)

        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.outcome, NativeActionOutcome.SUCCESS)
        self.assertEqual(len(invokes), 1)
        self.assertEqual(invokes[0].msg_type, INVOKE_TYPE)
        self.assertEqual(invokes[0].data["action"], "launch_camera_app")
        self.assertEqual(invokes[0].data["params"], {})

    def test_params_forwarded_for_sms(self):
        skill = _make_skill(responses=[_response(action="launch_sms_app")])
        invokes = _capture_invokes(skill)
        message = _node_message(action_supported=True, action="launch_sms_app")

        invoke_native_action(skill, message, NodeNativeAction.LAUNCH_SMS_APP,
                             params={"to": "5551234567", "body": "On my way"})

        self.assertEqual(invokes[0].data["params"],
                         {"to": "5551234567", "body": "On my way"})

    def test_success_silent_by_default(self):
        skill = _make_skill(responses=[_response(status="success")])
        message = _node_message(action_supported=True)

        invoke_native_action(skill, message, NodeNativeAction.LAUNCH_CAMERA_APP)

        skill.speak.assert_not_called()
        skill.speak_dialog.assert_not_called()

    def test_success_confirms_when_setting_enabled(self):
        skill = _make_skill(settings={"confirm_on_success": True},
                            responses=[_response(status="success")])
        message = _node_message(action_supported=True)

        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.outcome, NativeActionOutcome.SUCCESS)
        key, _ = _spoken(skill)
        self.assertEqual(key, "native_action_success")

    def test_error_response_speaks_failure_with_code_and_message(self):
        response = _response(status="error",
                             error={"code": "unavailable",
                                    "message": "No camera app."})
        skill = _make_skill(responses=[response])
        message = _node_message(action_supported=True)

        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.outcome, NativeActionOutcome.ERROR)
        self.assertEqual(result.error_code, NativeActionErrorCode.UNAVAILABLE)
        key, data = _spoken(skill)
        self.assertEqual(key, "native_action_error")
        self.assertEqual(data, {"action": "launch_camera_app",
                                "description": "the camera app",
                                "code": "unavailable",
                                "message": "No camera app."})

    def test_unknown_error_code_maps_to_internal_error(self):
        response = _response(status="error",
                             error={"code": "made_up_code", "message": "?"})
        skill = _make_skill(responses=[response])
        message = _node_message(action_supported=True)

        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.error_code,
                         NativeActionErrorCode.INTERNAL_ERROR)
        _, data = _spoken(skill)
        self.assertEqual(data["code"], "internal_error")

    # --- response waiting -------------------------------------------------

    def test_response_landing_before_emit_returns_is_caught(self):
        # The default 10s camera timeout stays in place: if the synchronous
        # reply were missed, this test would take 10s and report TIMEOUT.
        skill = _make_skill(responses=[_response(status="success")])
        message = _node_message(action_supported=True)

        start = time.monotonic()
        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.outcome, NativeActionOutcome.SUCCESS)
        self.assertLess(time.monotonic() - start, 1.0)

    def test_late_response_within_deadline_is_caught(self):
        skill = _make_skill(settings={"per_action_timeouts":
                                      {"launch_camera_app": 1}})
        message = _node_message(action_supported=True)
        threading.Timer(0.1, lambda: skill.bus.emit(_response())).start()

        start = time.monotonic()
        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.outcome, NativeActionOutcome.SUCCESS)
        self.assertLess(time.monotonic() - start, 1.0)

    def test_timeout_waits_for_full_deadline_then_speaks(self):
        skill = _make_skill(settings={"per_action_timeouts":
                                      {"launch_camera_app": 0.5}})
        message = _node_message(action_supported=True)

        start = time.monotonic()
        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)
        elapsed = time.monotonic() - start

        self.assertEqual(result.outcome, NativeActionOutcome.TIMEOUT)
        self.assertGreaterEqual(elapsed, 0.5)
        self.assertLess(elapsed, 1.5)
        key, _ = _spoken(skill)
        self.assertEqual(key, "native_action_timeout")

    def test_wrong_action_then_right_action_back_to_back(self):
        # Both replies land synchronously with no gap; the waiter must keep
        # listening through the first without re-subscribing.
        skill = _make_skill(responses=[_response(action="launch_clock_app"),
                                       _response(action="launch_camera_app")])
        message = _node_message(action_supported=True)

        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.outcome, NativeActionOutcome.SUCCESS)

    def test_mismatched_action_only_times_out(self):
        skill = _make_skill(settings=QUICK_TIMEOUTS,
                            responses=[_response(action="launch_clock_app")])
        message = _node_message(action_supported=True)

        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.outcome, NativeActionOutcome.TIMEOUT)

    def test_mismatched_session_only_times_out(self):
        skill = _make_skill(settings=QUICK_TIMEOUTS,
                            responses=[_response(session_id="node-other")])
        message = _node_message(action_supported=True)

        result = invoke_native_action(skill, message,
                                      NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(result.outcome, NativeActionOutcome.TIMEOUT)

    def test_response_handler_removed_after_success(self):
        skill = _make_skill(responses=[_response(status="success")])
        message = _node_message(action_supported=True)

        invoke_native_action(skill, message, NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(skill.bus.ee.listeners(RESPONSE_TYPE), [])

    def test_response_handler_removed_after_timeout(self):
        skill = _make_skill(settings=QUICK_TIMEOUTS)
        message = _node_message(action_supported=True)

        invoke_native_action(skill, message, NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertEqual(skill.bus.ee.listeners(RESPONSE_TYPE), [])

    # --- timeouts ---------------------------------------------------------

    def test_per_action_timeout_override_used(self):
        skill = _make_skill(settings={"per_action_timeouts":
                                      {"launch_camera_app": 1.5}})

        self.assertEqual(_resolve_timeout(skill, "launch_camera_app"), 1.5)

    def test_default_timeout_used_when_no_override(self):
        skill = _make_skill()

        self.assertEqual(_resolve_timeout(skill, "launch_camera_app"), 10)
        self.assertEqual(_resolve_timeout(skill, "launch_sms_app"), 5)

    def test_invalid_timeout_override_falls_back_with_warning(self):
        skill = _make_skill(settings={"per_action_timeouts":
                                      {"launch_camera_app": "soon"}})

        with patch("neon_utils.native_actions.LOG") as mock_log:
            timeout = _resolve_timeout(skill, "launch_camera_app")

        self.assertEqual(timeout, 10)
        mock_log.warning.assert_called_once()

    # --- dialog -----------------------------------------------------------

    def test_action_dialog_localizes_description(self):
        skill = _make_skill()
        skill.dialog_renderer = _renderer({"launch_camera_app": ["la cámara"]})
        message = _node_message(action_supported=False)

        invoke_native_action(skill, message, NodeNativeAction.LAUNCH_CAMERA_APP)

        _, data = _spoken(skill)
        self.assertEqual(data["description"], "la cámara")

    def test_missing_action_dialog_speaks_raw_key(self):
        # Standard OVOS behavior for a missing dialog file, and the cue a
        # skill author gets that `launch_camera_app.dialog` is absent.
        skill = _make_skill()
        skill.dialog_renderer = _renderer({})
        message = _node_message(action_supported=False)

        invoke_native_action(skill, message, NodeNativeAction.LAUNCH_CAMERA_APP)

        _, data = _spoken(skill)
        self.assertEqual(data["description"], "launch_camera_app")

    def test_no_dialog_renderer_speaks_raw_key_with_warning(self):
        skill = _make_skill()
        skill.dialog_renderer = None
        message = _node_message(action_supported=False)

        with patch("neon_utils.native_actions.LOG") as mock_log:
            invoke_native_action(skill, message,
                                 NodeNativeAction.LAUNCH_CAMERA_APP)

        _, data = _spoken(skill)
        self.assertEqual(data["description"], "launch_camera_app")
        mock_log.warning.assert_called_once()

    def test_speaks_with_triggering_message(self):
        skill = _make_skill()
        message = _node_message(action_supported=False)

        invoke_native_action(skill, message, NodeNativeAction.LAUNCH_CAMERA_APP)

        self.assertIs(skill.speak_dialog.call_args[1]["message"], message)


if __name__ == '__main__':
    unittest.main()
