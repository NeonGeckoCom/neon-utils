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
from typing import Optional
from urllib.parse import urlparse
from neon_utils.logger import LOG


def find_neon_git_token(base_path: str = "~/") -> str:
    """
    Searches environment variables and standard locations for a text file with a Github token.
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
        if os.environ.get("GITHUB_TOKEN"):
            return os.environ.get("GITHUB_TOKEN")
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


def find_generic_keyfile(base_path: str, filename: str) -> str:
    """
    Locates a generic text keyfile
    Args:
        base_path: Base directory to check in addition to XDG directories (default ~/)
        filename: File basename to read
    Returns:
        str contents of located file
    """
    path_to_check = os.path.expanduser(base_path)
    paths_to_check = (path_to_check,
                      os.path.join(path_to_check, filename),
                      os.path.expanduser(f"~/.local/share/neon/{filename}"))
    for path in paths_to_check:
        if os.path.isfile(path):
            try:
                with open(path, "r") as f:
                    credential = f.read().strip()
                return credential
            except Exception as e:
                LOG.error(f"Invalid credential found at: {path}")
                raise e
    raise FileNotFoundError(f"No credentials found in default locations or path: {path_to_check}")


def find_neon_wolfram_key(base_path: str = "~/") -> str:
    """
    Locates Wolfram|Alpha API key
    Args:
        base_path: Base directory to check in addition to XDG directories (default ~/)
    Returns:
        str Wolfram|Alpha API key
    """
    return find_generic_keyfile(base_path, "wolfram.txt")


def find_neon_alpha_vantage_key(base_path: str = "~/") -> str:
    """
    Locates Alpha Vantage API key
    Args:
        base_path: Base directory to check in addition to XDG directories (default ~/)
    Returns:
        str Alpha Vantage API key
    """
    return find_generic_keyfile(base_path, "alpha_vantage.txt")


def find_neon_owm_key(base_path: str = "~/") -> str:
    """
    Locates Open Weather Map key
    Args:
        base_path: Base directory to check in addition to XDG directories (default ~/)
    Returns:
        str Open Weather Map API key
    """
    return find_generic_keyfile(base_path, "owm.txt")


def populate_amazon_keys_config(aws_keys: dict, config_path: Optional[str] = None):
    """
    Populates configuration with the specified Amazon keys to be referenced by tts/translation modules.
    Args:
        aws_keys: Dict of aws credentials to use (returned by `find_neon_aws_keys()`)
        config_path: Override path to ngi_local_conf
    """
    from neon_utils.configuration_utils import NGIConfig

    assert "aws_access_key_id" in aws_keys
    assert "aws_secret_access_key" in aws_keys

    if not aws_keys.get("aws_access_key_id") or not aws_keys.get("aws_secret_access_key"):
        raise ValueError

    local_conf = NGIConfig("ngi_local_conf", config_path, True)
    aws_config = local_conf["tts"]["amazon"]
    aws_config = {**aws_config, **aws_keys}
    local_conf["tts"]["amazon"] = aws_config
    local_conf.write_changes()
    # TODO: This should be depreciated and references moved to neon_auth_config DM


def populate_github_token_config(token: str, config_path: Optional[str] = None):
    """
    Populates configuration with the specified github token for later reference.
    Args:
        token: String Github token
        config_path: Override path to ngi_local_conf
    """
    from neon_utils.configuration_utils import NGIConfig

    assert token

    local_conf = NGIConfig("ngi_local_conf", config_path, True)
    local_conf["skills"]["neon_token"] = token
    local_conf.write_changes()
    # TODO: This should be depreciated and references moved to neon_auth_config DM


def repo_is_neon(repo_url: str) -> bool:
    """
    Determines if the specified repository url is part of the NeonGeckoCom org on github
    Args:
        repo_url: string url to check
    Returns:
        True if the repository URL is known to be accessible using a neon auth key
    """
    url = urlparse(repo_url)
    if not url.scheme or not url.netloc:
        raise ValueError(f"{repo_url} is not a valid url")
    if any([x for x in ("github.com", "githubusercontent.com") if x in url.netloc]):
        try:
            author = url.path.split('/')[1]
        except IndexError:
            raise ValueError(f"{repo_url} is not a valid github url")
        if author.lower() == "neongeckocom":
            return True
        elif author.lower().startswith("neon"):  # TODO: Get token and scrape org? DM
            LOG.info(f"Assuming repository uses Neon auth: {repo_url}")
            return True
    return False


def build_new_auth_config(key_path: str = "~/") -> dict:
    """
    Constructs a dict of authentication key data by locating credential files in the specified path
    :param key_path: path to locate key files (default locations checked in addition)
    :return: dict of located authentication keys
    """
    key_path = key_path or "~/"
    auth_config = dict()
    try:
        auth_config["github"] = {"token": find_neon_git_token(key_path)}
    except Exception as e:
        LOG.error(e)
    try:
        auth_config["amazon"] = find_neon_aws_keys(key_path)
    except Exception as e:
        LOG.error(e)
    try:
        auth_config["wolfram"] = {"app_id": find_neon_wolfram_key(key_path)}
    except Exception as e:
        LOG.error(e)
    try:
        auth_config["google"] = find_neon_google_keys(key_path)
    except Exception as e:
        LOG.error(e)
    try:
        auth_config["alpha_vantage"] = {"api_key": find_neon_alpha_vantage_key(key_path)}
    except Exception as e:
        LOG.error(e)
    try:
        auth_config["owm"] = {"api_key": find_neon_owm_key(key_path)}
    except Exception as e:
        LOG.error(e)

    return auth_config
