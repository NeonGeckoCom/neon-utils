from skill_override_functions import *


def stub_missing_parameters(skill):
    skill.server = False
    # TODO: Iterate over functions instead of individual DM
    skill.neon_in_request = neon_in_request
    skill.neon_must_respond = neon_must_respond
