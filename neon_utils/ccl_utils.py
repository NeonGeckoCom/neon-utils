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

import pickle

from os import remove
from os.path import isfile, exists, isdir, expanduser, join, basename, splitext, dirname
from typing import Optional

from neon_utils.file_utils import decode_base64_string_to_file
from neon_utils.logger import LOG

try:
    from neon_script_parser import ScriptParser
except ImportError:
    ScriptParser = None
    from neon_utils.mq_utils import get_mq_response, send_mq_request


def parse_nct_to_ncs(nct_file_path: str, ncs_file_path: Optional[str] = None,
                     meta: dict = None, overwrite_existing: bool = False):
    """
    Parses an input .nct file into an .ncs file.
    :param nct_file_path: Path to the input script file to be parsed
    :param ncs_file_path: Path to output the parsed script
    :param meta: Optional dict meta to include in output
    :param overwrite_existing: Boolean flag to allow for overwriting an existing .ncs file.
    """
    nct_file_path = expanduser(nct_file_path)
    if not ncs_file_path:
        ncs_file_path = dirname(nct_file_path)
    ncs_file_path = expanduser(ncs_file_path)

    if not isfile(nct_file_path):
        raise FileNotFoundError(f"{nct_file_path} is not a file")
    if not nct_file_path.endswith(".nct"):
        raise ValueError(f"{nct_file_path} is not a nct file.")
    if isdir(ncs_file_path):
        ncs_file_path = join(ncs_file_path, splitext(basename(nct_file_path))[0] + ".ncs")

    if exists(ncs_file_path):
        if overwrite_existing:
            LOG.warning(f"File exists and will be overwritten: {ncs_file_path}")
            remove(ncs_file_path)
        else:
            raise FileExistsError(f"{ncs_file_path} already exists")

    if not ncs_file_path.endswith(".ncs"):
        raise ValueError(f"{ncs_file_path} is not a ncs file.")
    LOG.debug(f"Output path = {ncs_file_path}")
    if ScriptParser:
        ScriptParser().parse_script_to_file(nct_file_path, ncs_file_path, meta)
    else:
        with open(nct_file_path) as f:
            text = f.read()

        encoded_script = get_compiled_script_via_mq(text, meta)
        decode_base64_string_to_file(encoded_script, ncs_file_path)


def parse_text_to_ncs(text: str, ncs_file_path: str,
                      meta: dict = None, overwrite_existing: bool = False):
    """
    Parses input text into an .ncs file.
    :param text: Raw text to be parsed into a .ncs script
    :param ncs_file_path: Path to output the parsed script
    :param meta: Optional dict meta to include in output
    :param overwrite_existing: Boolean flag to allow for overwriting an existing .ncs file.
    """
    ncs_file_path = expanduser(ncs_file_path)

    if exists(ncs_file_path):
        if overwrite_existing:
            LOG.warning(f"File exists and will be overwritten: {ncs_file_path}")
            remove(ncs_file_path)
        else:
            raise FileExistsError(f"{ncs_file_path} already exists")

    LOG.debug(f"Output path = {ncs_file_path}")
    if ScriptParser:
        ScriptParser().parse_text_to_file(text, ncs_file_path, meta)
    else:
        encoded_script = get_compiled_script_via_mq(text, meta)
        decode_base64_string_to_file(encoded_script, ncs_file_path)


def load_ncs_file(ncs_file_path: str) -> dict:
    """
    Loads the passed ncs file and returns the resulting dict
    :param ncs_file_path: path to file to load
    :return: parsed dict representation of a ccl script
    """
    ncs_file_path = expanduser(ncs_file_path)

    if not isfile(ncs_file_path):
        raise FileNotFoundError(f"{ncs_file_path} is not a file.")
    if not ncs_file_path.endswith(".ncs"):
        raise ValueError(f"{ncs_file_path} is not a ncs file.")

    try:
        with open(ncs_file_path, 'rb') as f:
            parsed = pickle.load(f)
    except EOFError as e:
        LOG.error(e)
        raise ValueError(f"{ncs_file_path} is not a ncs file.")
    if isinstance(parsed, list):
        parsed = {"formatted_script": parsed[0],
                  "speaker_dict": parsed[1],
                  "variables": parsed[2],
                  "loops_dict": parsed[3],
                  "goto_tags": parsed[4],
                  "timeout": parsed[5],
                  "timeout_action": parsed[6],
                  "script_meta": parsed[9]}
    elif not isinstance(parsed, dict):
        raise ValueError(f"Invalid contents read from ncs_file. type={type(parsed)}")
    return parsed


def get_compiled_script_via_mq(text: str, meta: Optional[dict]) -> str:
    data = {"text": text,
            "meta": meta}
    resp = send_mq_request("/neon_script_parser", data, "neon_script_parser_input", timeout=45)
    return resp["parsed_file"]
