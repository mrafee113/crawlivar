from django.core.exceptions import ValidationError

import re


def phone_validator(value):
    regex = r"[0-9]{11}"
    match = re.fullmatch(regex, value)
    if match is None:
        raise ValidationError("phone number must be exactly 10 characters")
