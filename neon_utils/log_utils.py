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

import logging

from datetime import datetime, timedelta
from typing import Optional, Union

from neon_utils.logger import LOG
from neon_utils.configuration_utils import get_neon_local_config

LOG_DIR = os.path.expanduser(get_neon_local_config()["dirVars"]["logsDir"])


def remove_old_logs(log_dir: str = LOG_DIR, history_to_retain: timedelta = timedelta(weeks=6)):
    """
    Removes archived logs older than the specified history timedelta
    Args:
        log_dir: Path to archived logs
        history_to_retain: Timedelta of history to retain
    """
    from shutil import rmtree
    for archive in os.listdir(log_dir):
        archive_path = os.path.join(log_dir, archive)
        if not os.path.isdir(archive_path):
            continue
        if datetime.now() - datetime.fromtimestamp(os.path.getmtime(archive_path)) > history_to_retain:
            LOG.info(f"removing {archive}")
            rmtree(archive_path)


def archive_logs(log_dir: str = LOG_DIR, archive_dir: Optional[str] = None):
    """
    Archives the logs in the specified log_dir to log_dir/dir_name
    Args:
        log_dir: Path to log files to be archived
        archive_dir: Directory to archive logs to (defaults to formatted time)
    """
    from glob import glob
    from os.path import join, basename
    from os import makedirs
    from shutil import move
    default_dirname = "logs--" + datetime.now().strftime("%Y-%m-%d--%H:%M:%S")
    archive_dir = join(log_dir, archive_dir or default_dirname)
    makedirs(archive_dir, exist_ok=True)
    for file in glob(join(log_dir, "*.log")):
        if basename(file) != "start.log":
            move(file, archive_dir)


def get_logger(log_name: str, log_dir: str = LOG_DIR, std_out: bool = False) -> logging.Logger:
    """
    Get a logger with the specified name and write to the specified log_dir and optionally std_out
    Args:
        log_name: Name of log (also used as log filename)
        log_dir: Directory to write log file to
        std_out: Flag to include logs in STDOUT

    Returns:
        Logger with the specified handlers
    """
    LOG.init({"path": log_dir or "stdout"})
    LOG.name = log_name
    log = LOG.create_logger(log_name, std_out)
    return log


def get_log_file_for_module(module_name: Union[str, list]) -> str:
    """
    Gets the default log basename for the requested module
    Args:
        module_name: Runnable argument passed to Popen
            (i.e. neon_speech_client, [python3, -m, mycroft.skills])

    Returns:
        Path to logfile
    """
    if isinstance(module_name, list):
        module_name = module_name[-1]
    if module_name.startswith("neon_speech"):
        log_name = "voice.log"
    elif module_name.startswith("neon_audio"):
        log_name = "audio.log"
    elif module_name.startswith("neon_enclosure"):
        log_name = "enclosure.log"
    elif any(x for x in ("neon_messagebus", "neon_core.messagebus", "mycroft.messagebus") if module_name.startswith(x)):
        log_name = "bus.log"
    elif any(x for x in ("neon_skills", "neon_core.skills", "mycroft.skills") if module_name.startswith(x)):
        log_name = "skills.log"
    elif any(x for x in ("neon_gui", "neon_core.gui") if module_name.startswith(x)):
        log_name = "display.log"
    elif module_name == "neon_core_client":
        log_name = "client.log"
    elif module_name == "neon_core_server":
        log_name = "server.log"
    elif module_name == "mycroft-gui-app":
        log_name = "gui.log"
    else:
        log_name = "extras.log"

    return os.path.join(LOG_DIR, log_name)
