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
from datetime import timedelta, datetime
from typing import Optional

from ovos_utils.signal import ensure_directory_exists

from neon_utils.logger import LOG


def get_likes_from_csv(file: str, user: Optional[str],
                       line_limit: int = 500, date_limit: Optional[timedelta] = timedelta(days=7)) -> dict:
    """
    Reads likes data from the specified csv file (default: selected_ts.csv). The lesser of the passed limits will be
    evaluated. Pass `None` for user to get data for all users within specified limits
    :param file: path to csv file to evaluate
    :param user: username associated with likes (None for all)
    :param line_limit: maximum number of lines to process
    :param date_limit: maximum time history to process
    :return: dict of likes data
    """
    file = os.path.expanduser(file)
    if not os.path.isfile(file):
        raise FileNotFoundError
    with open(file, "r") as csv:
        lines_to_evaluate = csv.readlines()

    if line_limit and len(lines_to_evaluate) > line_limit:
        lines_to_evaluate = lines_to_evaluate[-line_limit:]
    else:
        lines_to_evaluate = lines_to_evaluate[1:]
    lines_to_evaluate.reverse()
    likes = {}
    for line in lines_to_evaluate:
        date_str, profile, device, phrase, transcription_filename, brand = line.rstrip("\n").split(",", 5)
        # Date,Profile,Device,Phrase,Instance,Brand
        if date_limit and datetime.now() - datetime.strptime(date_str, "%Y-%m-%d") > date_limit:
            # Stop parsing once we reach our oldest date limit
            break
        if user and profile != user:
            # Ignore anything from other users than requested
            continue

        transcription_subdir = f"{profile}-{date_str}"
        if brand not in likes.keys():
            likes[brand] = []
        likes[brand].append({"date": date_str,
                             "user": profile,
                             "file": os.path.join(transcription_subdir, transcription_filename),
                             "utterance": phrase})
    return likes


def update_csv(info: list, location: str):
    """
    Neon function used to generate CSV files for transcripts
    :param info: list of data to export to csv
    :param location: fully defined file path
    :return:
    """
    import csv

    def _write_line(data, file):
        try:
            with open(file, 'a+') as to_write:
                writer = csv.writer(to_write)
                writer.writerow(data)
        except IOError as e:
            LOG.error(e)

    location = os.path.expanduser(location)

    # Check if file exists with first row
    csv_dir = os.path.dirname(location)
    if not os.path.isfile(location):
        os.makedirs(csv_dir, exist_ok=True)
        if os.path.basename(location) == "full_ts.csv":
            list_transcription_headers = ["Date", "Time", "Profile", "Device", "Input", "Location", "Wav_Length"]
            _write_line(list_transcription_headers, location)
        elif os.path.basename(location) == "selected_ts.csv":
            list_selected_headers = ["Date", "Profile", "Device", "Phrase", "Instance", "Brand"]
            _write_line(list_selected_headers, location)
        elif os.path.basename(location) == "running_out.csv":
            list_selected_headers = ["Date", "Profile", "Device", "Phrase", "Instance", "Item"]
            _write_line(list_selected_headers, location)
        elif os.path.basename(location) == "symptom_checker.csv":
            list_selected_headers = ["Date", "Profile", "Agent", "Device", "Phrase", "Tags", "Location"]
            _write_line(list_selected_headers, location)
    # Write out  data
    _write_line(info, location)


def write_transcript_file(utterance: str, path: str, transcript_name: str, username: str, timestamp: float) -> str:
    """
    Writes out a transcript at the specified path and filename
    :param utterance: Text to transcribe
    :param path: Path to transcriptions
    :param transcript_name: Name of transcript (directory name)
    :param username: User associated with utterance
    :param timestamp: Timestamp associated with utterance
    :return: formatted line written to the transcript
    """
    import datetime

    path = os.path.expanduser(path)
    ensure_directory_exists(path, transcript_name)

    f_time = str(datetime.datetime.fromtimestamp(timestamp))
    f_date = str(datetime.date.fromtimestamp(timestamp))
    shared_file = os.path.join(path, transcript_name, f"{f_date}.txt")
    person_file = os.path.join(path, transcript_name, f"{username}-{f_date}.txt")

    formatted_line = f"{username}-{f_time} {utterance}\n"

    with open(shared_file, 'a+') as shared:
        shared.write(formatted_line)
    with open(person_file, 'a+') as person:
        person.write(formatted_line)
    return formatted_line


def get_transcript_file(path: str, transcript_name: str, username: Optional[str], f_date: str) -> Optional[str]:
    """
    Returns the path to a requested transcript file if exists
    :param path: Path to transcripts
    :param transcript_name: Name of transcript to return
        (ts_selected_transcripts, running_out_transcripts, ts_transcripts, etc.)
    :param username: Username requested (None for combined daily transcripts)
    :param f_date: String formatted date requested (YYYY-MM-DD)
    :return: Path to requested transcript (None if not exists)
    """
    path = os.path.expanduser(path)
    if username:
        transcript_file = os.path.join(path, transcript_name, f"{username}-{f_date}.txt")
    else:
        transcript_file = os.path.join(path, transcript_name, f"{f_date}.txt")

    if os.path.isfile(transcript_file):
        return transcript_file
    else:
        return None
