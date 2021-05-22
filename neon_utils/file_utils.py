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

import glob
import os
import base64
import wave
from tempfile import mkstemp

from typing import Optional
from pydub import AudioSegment
from ovos_utils.signal import ensure_directory_exists

from neon_utils import LOG


def encode_file_to_base64_string(path: str) -> str:
    """
    Encodes a file to a base64 string (useful for passing file data over a messagebus)
    :param path: Path to file to be encoded
    :return: encoded string
    """
    if not isinstance(path, str):
        raise TypeError
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        LOG.error(f"File Not Found: {path}")
        raise FileNotFoundError
    with open(path, "rb") as file_in:
        encoded = base64.b64encode(file_in.read()).decode("utf-8")
    return encoded


def decode_base64_string_to_file(encoded_string: str, output_path: str) -> str:
    """
    Writes out a base64 string to a file object at the specified path
    :param encoded_string: Base64 encoded string
    :param output_path: Path to file to write (throws exception if file exists)
    :return: Path to output file
    """
    if not isinstance(output_path, str):
        raise TypeError
    output_path = os.path.expanduser(output_path)
    if os.path.isfile(output_path):
        LOG.error(f"File already exists: {output_path}")
        raise FileExistsError
    ensure_directory_exists(os.path.dirname(output_path))
    with open(output_path, "wb+") as file_out:
        byte_data = base64.b64decode(encoded_string.encode("utf-8"))
        file_out.write(byte_data)
    return output_path


def get_most_recent_file_in_dir(path: str, ext: Optional[str] = None) -> Optional[str]:
    """
    Gets the most recently created file in the specified path
    :param path: File path or glob pattern to check
    :param ext: File extension
    :return: Path to newest file in specified path with specified extension (None if no files in path)
    """
    if os.path.isdir(path):
        path = f"{path}/*"
    list_of_files = glob.glob(path)  # * means all if need specific format then *.csv
    if ext:
        if not ext.startswith("."):
            ext = f".{ext}"
        list_of_files = [file for file in list_of_files if os.path.splitext(file)[1] == ext]
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getctime)
        return latest_file
    else:
        return None


def get_file_as_wav(audio_file: str, desired_sample_rate: int, desired_sample_width: int = 2) -> wave.Wave_read:
    """
    Gets a wav file for the passed audio file.
    Args:
        audio_file: Path to audio file in arbitrary format
        desired_sample_rate: sample rate at which returned wav data should be encoded
        desired_sample_width: sample width at which returned wav data should be encoded
    Returns:
        Wave_read object encoded at the desired_sample_rate
    """

    audio_file = os.path.expanduser(audio_file)
    if not os.path.isfile(audio_file):
        raise FileNotFoundError
    try:
        file = wave.open(audio_file, 'rb')
        sample_rate = file.getframerate()
        sample_width = file.getsampwidth()
        if sample_rate == desired_sample_rate and sample_width == desired_sample_width:
            return file
    except wave.Error:
        pass
    except Exception as e:
        raise e
    audio = AudioSegment.from_file(audio_file)
    audio = audio.set_frame_rate(desired_sample_rate).set_sample_width(desired_sample_width)
    _, tempfile = mkstemp()
    audio.export(tempfile, format='wav').close()
    return wave.open(tempfile, 'rb')


def get_audio_file_stream(wav_file: str, sample_rate: int = 16000):
    """
    Creates a FileStream object for the specified wav_file with the specified output sample_rate.
    Args:
        wav_file: Path to file to read
        sample_rate: Desired output sample rate (None for wav_file sample rate)

    Returns:
        FileStream object for the passed audio file
    """
    class FileStream:
        MIN_S_TO_DEBUG = 5.0

        # How long between printing debug info to screen
        UPDATE_INTERVAL_S = 1.0

        def __init__(self, file_name):
            self.file = get_file_as_wav(file_name, sample_rate)
            self.sample_rate = self.file.getframerate()
            # if sample_rate and self.sample_rate != sample_rate:
            #     sound = AudioSegment.from_file(file_name, format='wav', frame_rate=self.sample_rate)
            #     sound = sound.set_frame_rate(sample_rate)
            #     _, tempfile = mkstemp()
            #     sound.export(tempfile, format='wav')
            #     self.file = wave.open(tempfile, 'rb')
            #     self.sample_rate = self.file.getframerate()
            self.size = self.file.getnframes()
            self.sample_width = self.file.getsampwidth()
            self.last_update_time = 0.0

            self.total_s = self.size / self.sample_rate / self.sample_width

        def calc_progress(self):
            return float(self.file.tell()) / self.size

        def read(self, chunk_size):

            progress = self.calc_progress()
            if progress == 1.0:
                raise EOFError

            return self.file.readframes(chunk_size)

        def close(self):
            self.file.close()

    if not os.path.isfile(wav_file):
        raise FileNotFoundError
    try:
        return FileStream(wav_file)
    except Exception as e:
        raise e
