# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_signup_invalid_password[hi] 1"] = {
    "body": {
        "data": None,
        "message": """Parameter validation failed:
Invalid length for parameter Password, value: 2, valid range: 6-inf""",
    },
    "statusCode": 400,
}

snapshots["test_signup_invalid_password[H3l!o W] 1"] = {
    "body": {
        "data": None,
        "message": "The password must be at least 8 characters long, have both upper and lower case letters, and at least one special character.",
    },
    "statusCode": 400,
}

snapshots["test_signup_invalid_password[h3llo world!] 1"] = {
    "body": {
        "data": None,
        "message": "The password must be at least 8 characters long, have both upper and lower case letters, and at least one special character.",
    },
    "statusCode": 400,
}

snapshots["test_signup_invalid_password[H3LLO WORLD!] 1"] = {
    "body": {
        "data": None,
        "message": "The password must be at least 8 characters long, have both upper and lower case letters, and at least one special character.",
    },
    "statusCode": 400,
}

snapshots["test_signup_invalid_password[H3llo World] 1"] = {
    "body": {
        "data": None,
        "message": "The password must be at least 8 characters long, have both upper and lower case letters, and at least one special character.",
    },
    "statusCode": 400,
}

snapshots["test_signup_invalid_invitation_code 1"] = {
    "body": {
        "data": None,
        "message": "Invalid invitation code. Please contact an administrator.",
    },
    "statusCode": 400,
}

snapshots["test_signup 1"] = {
    "body": {
        "data": None,
        "message": "Your account has been created. Please check your email for the confirmation code.",
    },
    "statusCode": 200,
}

snapshots["test_confirm_signup_invalid_user 1"] = {
    "body": {
        "data": None,
        "message": "Username test.user@pogam-estate.com doesn't exist.",
    },
    "statusCode": 400,
}

snapshots["test_confirm_signup_already_confirmed 1"] = {
    "body": {"data": None, "message": "User is already confirmed."},
    "statusCode": 200,
}

snapshots["test_forgot_password_invalid_user 1"] = {
    "body": {
        "data": None,
        "message": "Username test.user@pogam-estate.com doesn't exist.",
    },
    "statusCode": 400,
}

snapshots["test_forgot_password_unconfirmed_user 1"] = {
    "body": {
        "data": None,
        "message": "Username test.user@pogam-estate.com is not yet confirmed.",
    },
    "statusCode": 400,
}

snapshots["test_confirm_signup_invalid_verification_code 1"] = {
    "body": {"data": None, "message": "Invalid confirmation code."},
    "statusCode": 400,
}

snapshots["test_resend_verification_code[not_found-400] 1"] = {
    "body": {
        "data": None,
        "message": "Username test.user.foo@pogam-estate.com doesn't exist.",
    },
    "statusCode": 400,
}

snapshots["test_resend_verification_code[unconfirmed-200] 1"] = {
    "body": {
        "data": None,
        "message": "The confirmation code has been resent. Please check your email.",
    },
    "statusCode": 200,
}

snapshots["test_resend_verification_code[confirmed-200] 1"] = {
    "body": {"data": None, "message": "User is already confirmed."},
    "statusCode": 200,
}

snapshots["test_forgot_password 1"] = {
    "body": {
        "data": None,
        "message": "Please check your registered email for the password reset code.",
    },
    "statusCode": 200,
}

snapshots["test_confirm_signup[not_found-400] 1"] = {
    "body": {
        "data": None,
        "message": "Username test.user.foo@pogam-estate.com doesn't exist.",
    },
    "statusCode": 400,
}

snapshots["test_confirm_signup[unconfirmed-400] 1"] = {
    "body": {"data": None, "message": "Invalid confirmation code."},
    "statusCode": 400,
}
