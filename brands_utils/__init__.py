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


def get_likes_from_csv(file: str, user: str, line_limit: int = 500, date_limit: timedelta = timedelta(days=7)) -> dict:
    """
    Reads likes data from the specified csv file (default: selected_ts.csv). The lesser of the passed limits will be
    evaluated. Pass `None` for user to get data for all users within specified limits
    :param file: path to csv file to evaluate
    :param user: username associated with likes (None for all)
    :param line_limit: maximum number of lines to process
    :param date_limit: maximum time history to process
    :return: dict of likes data
    """
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
