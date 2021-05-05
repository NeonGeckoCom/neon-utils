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

import json
import os.path

from neon_utils.logger import LOG


def find_neon_git_token(base_path: str = "~/") -> str:
    """
    Searches standard locations for a text file with a Github token.
    Args:
        base_path: Base directory to check in addition to XDG directories (default ~/)
    Returns:
        Github token string
    """
    path_to_check = os.path.expanduser(base_path)
    paths_to_check = (path_to_check,
                      os.path.join(path_to_check, "token.txt"),
                      os.path.expanduser("~/.local/share/neon/git_token.txt"),
                      os.path.expanduser("~/.local/share/neon/token.txt"))
    cred_file = None
    for path in paths_to_check:
        if os.path.isfile(path):
            cred_file = path
            break
    if not cred_file:
        raise FileNotFoundError("Could not locate github credentials")

    with open(cred_file) as f:
        git_token = f.read().strip('\n').strip()
    if not git_token:
        raise ValueError(f"Empty Git token specified in {cred_file}")
    return git_token


def find_neon_aws_keys(base_path: str = "~/") -> dict:
    """
    Searches standard locations for AWS credentials
    Args:
        base_path: Base directory to check in addition to XDG directories (default ~/)
    Returns:
        dict containing 'aws_access_key_id' and 'aws_secret_access_key'
    """
    path_to_check = os.path.expanduser(base_path)
    csv_paths = (path_to_check,
                 os.path.join(path_to_check, "accessKeys.csv"))
    sys_path = os.path.expanduser("~/.aws/credentials")
    json_path = os.path.expanduser("~/.local/share/neon/aws.json")

    amazon_creds = None
    for path in csv_paths:
        if os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    aws_id, aws_key = f.readlines()[1].rstrip('\n').split(',', 1)
                    amazon_creds = {"aws_access_key_id": aws_id,
                                    "aws_secret_access_key": aws_key}

            except Exception as e:
                LOG.error(e)
                LOG.error(path)

    if not amazon_creds:
        if os.path.isfile(json_path):
            with open(json_path, "r") as f:
                amazon_creds = json.load(f)
        elif os.path.isfile(sys_path):
            with open(sys_path, "r") as f:
                for line in f.read().split("\n"):
                    if line.startswith("aws_access_key_id"):
                        aws_id = line.split("=", 1)[1].strip()
                    elif line.startswith("aws_secret_access_key"):
                        aws_key = line.split("=", 1)[1].strip()
            amazon_creds = {"aws_access_key_id": aws_id,
                            "aws_secret_access_key": aws_key}

    if not amazon_creds:
        raise FileNotFoundError(f"No aws credentials found in default locations or path: {path_to_check}")
    return amazon_creds


def find_neon_google_keys(base_path: str = "~/") -> dict:
    """
    Locates google json credentials and returns the parsed credentials as a dict
    Args:
        base_path: Base directory to check in addition to XDG directories (default ~/)
    Returns:
        dict Google json credential
    """
    path_to_check = os.path.expanduser(base_path)
    paths_to_check = (path_to_check,
                      os.path.join(path_to_check, "google.json"),
                      os.path.expanduser("~/.local/share/neon/google.json"))
    for path in paths_to_check:
        if os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    credential = json.load(f)
                return credential
            except Exception as e:
                LOG.error(f"Invalid google credential found at: {path}")
                raise e
    raise FileNotFoundError(f"No google credentials found in default locations or path: {path_to_check}")
