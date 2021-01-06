def neon_must_respond(message):
    return True


def neon_in_request(message):
    return True


def request_from_mobile(message):
    return True


def preference_brands(message):
    return {'ignored_brands': {},
            'favorite_brands': {},
            'specially_requested': {}}


def preference_user(message):
    return {}


def preference_location(message):
    return {}


def preference_unit(message):
    return {}


def preference_speech(message):
    return {}


def build_user_dict(message=None):
    merged_dict = {**preference_speech(message), **preference_user(message),
                   **preference_brands(message), **preference_location(message),
                   **preference_unit(message)}
    for key, value in merged_dict.items():
        if value == "":
            merged_dict[key] = -1
    return merged_dict


