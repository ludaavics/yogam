import json
import logging
import os
import subprocess
import time

import boto3
import pytest
import requests
from requests.compat import urljoin  # type: ignore

logger = logging.getLogger("pogam-tests")
here = os.path.dirname(__file__)
root_folder = os.path.abspath(os.path.join(here, ".."))
fixtures_folder = os.path.join(root_folder, "tests", "fixtures", "users-api")
service_folder = os.path.join(root_folder, "app", "users-api")


# ------------------------------------------------------------------------------------ #
#                                       Fixtures                                       #
# ------------------------------------------------------------------------------------ #

# --------------------------------------- Users -------------------------------------- #
@pytest.fixture
def user_email_unconfirmed():
    return "test.user.unconfirmed@pogam-estate.com"


@pytest.fixture
def user_email_not_found():
    return "test.user.foo@pogam-estate.com"


@pytest.fixture
def user_new_password():
    return "G00dbye World!"


@pytest.fixture
def user_invitation_code():
    return "test invitation code"


@pytest.fixture
def user_verification_code():
    return "test_verification_code"


@pytest.fixture
def user_unconfirmed(
    user_pool_id, user_pool_client_id, user_name, user_email_unconfirmed, user_password
):
    cognito = boto3.client("cognito-idp")
    cognito.sign_up(
        ClientId=user_pool_client_id,
        Username=user_email_unconfirmed,
        Password=user_password,
        UserAttributes=[
            {"Name": "name", "Value": user_name},
            {"Name": "email", "Value": user_email_unconfirmed},
        ],
        ValidationData=[
            {"Name": "email", "Value": user_email_unconfirmed},
            {"Name": "custom:username", "Value": user_email_unconfirmed},
        ],
    )
    time.sleep(0.5)
    yield
    cognito.admin_delete_user(UserPoolId=user_pool_id, Username=user_email_unconfirmed)
    time.sleep(0.5)


@pytest.fixture
def cleanup_users(user_pool_id):
    yield
    cognito = boto3.client("cognito-idp")
    has_next_page = True
    while has_next_page:
        page = cognito.list_users(UserPoolId=user_pool_id, Limit=60)
        for user in page["Users"]:
            cognito.admin_delete_user(
                UserPoolId=user_pool_id, Username=user["Username"]
            )
            time.sleep(0.5)
        has_next_page = "PaginationToken" in page


# ------------------------------------- Requests ------------------------------------- #
@pytest.fixture
def signup_request(user_name, user_email, user_password, user_invitation_code):
    def _signup_request(
        *,
        name=user_name,
        email=user_email,
        password=user_password,
        invitation_code=user_invitation_code,
    ):
        return {
            "username": email,
            "name": name,
            "email": email,
            "password": password,
            "invitation_code": invitation_code,
        }

    return _signup_request


@pytest.fixture
def resend_verification_request(user_email):
    def _resend_verification_request(*, email=user_email):
        return {"username": email}

    return _resend_verification_request


@pytest.fixture
def confirm_signup_request(user_email, user_verification_code):
    def _confirm_signup_request(
        *, email=user_email, verification_code=user_verification_code
    ):
        return {"username": email, "verification_code": verification_code}

    return _confirm_signup_request


@pytest.fixture
def forgot_password_request(user_email):
    def _forgot_password_request(*, email=user_email):
        return {"username": email}

    return _forgot_password_request


@pytest.fixture
def reset_password_request(
    user_email, user_new_password, user_verification_code,
):
    def _reset_password_request(
        *,
        email=user_email,
        new_password=user_new_password,
        verification_code=user_verification_code,
    ):
        return {
            "username": email,
            "password": new_password,
            "verification_code": verification_code,
        }

    return _reset_password_request


# -------------------------------------- Events -------------------------------------- #
@pytest.fixture
def authenticate_event(user_email, user_password):
    """API Gateway event to authenticate a user."""

    def _authenticate_event(
        email=user_email, password=user_password,
    ):
        with open(
            os.path.join(fixtures_folder, "authenticate-event-template.json"), "r"
        ) as f:
            event = json.loads(
                f.read().replace("[EMAIL]", email).replace("[PASSWORD]", password)
            )
        return event

    return _authenticate_event


@pytest.fixture
def profile_event(token, user_email, user_name):
    """API Gateway event to profile a user."""

    def _profile_event(token=token, email=user_email, name=user_name):
        with open(
            os.path.join(fixtures_folder, "profile-event-template.json"), "r"
        ) as f:
            event = json.loads(
                f.read()
                .replace("[TOKEN]", token)
                .replace("[EMAIL]", email)
                .replace("[NAME]", name)
            )
        return event

    return _profile_event


# ------------------------------------------------------------------------------------ #
#                                         Tests                                        #
# ------------------------------------------------------------------------------------ #
def api_request(api_host, method, resource, data=None, json=None):
    url = urljoin(api_host, resource)
    return getattr(requests, method)(url, data=data, json=json)


def api_assert_match(response, status_code, snapshot):
    if response.status_code != status_code:
        msg = (
            f"Got status code {response.status_code}, expected {status_code}:\n"
            f"{response.text}"
        )
        raise AssertionError(msg)
    snapshot.assert_match(response.text)


def sls_invoke(stage, function, data, folder=service_folder):
    return subprocess.run(
        [
            "sls",
            "invoke",
            "--stage",
            stage,
            "--function",
            function,
            "--data",
            json.dumps(data),
        ],
        cwd=folder,
        capture_output=True,
    )


def handler_assert_match(
    handler_response: subprocess.CompletedProcess,
    stage,
    iferror_message: str,
    status_code,
    snapshot,
):
    logger.debug(handler_response.stdout.decode("utf-8"))
    assert handler_response.returncode == 0, iferror_message
    api_response = json.loads(
        handler_response.stdout.decode("utf-8").replace(stage, "test")
    )
    body = json.loads(api_response.get("body"))
    data = body["data"]
    if isinstance(data, dict):
        data = {k: data[k] if "token" not in k else "===hidden-secret===" for k in data}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                if item.get("Name", None) == "sub":
                    item["Value"] = "===hidden-secret==="
    body["data"] = data
    api_response["body"] = body
    assert api_response["statusCode"] == status_code, api_response
    snapshot.assert_match(api_response)


@pytest.mark.aws
@pytest.mark.parametrize(
    "password, invitation_code_is_correct, status_code",
    [
        ("hi", True, 400),
        ("H3l!o W", True, 400),
        ("h3llo world!", True, 400),
        ("H3LLO WORLD!", True, 400),
        ("H3llo World", True, 400),
        ("H3llo World!", False, 400),
        ("H3llo World!", True, 200),
    ],
)
def test_signup(
    api_host,
    users_api_service,
    signup_request,
    password,
    user_invitation_code,
    invitation_code_is_correct,
    status_code,
    cleanup_users,
    snapshot,
):
    invitation_code = user_invitation_code if invitation_code_is_correct else "foobar"
    signup_request = signup_request(password=password, invitation_code=invitation_code)
    api_response = api_request(
        api_host, "post", "v1/users/signup", json=signup_request,
    )
    api_assert_match(api_response, status_code, snapshot)


@pytest.mark.aws
@pytest.mark.parametrize(
    "user_status, status_code",
    [("not_found", 400), ("unconfirmed", 200), ("confirmed", 200)],
)
def test_resend_verification_code(
    api_host,
    users_api_service,
    user_email_not_found,
    user_email_unconfirmed,
    user_email,
    user,
    user_unconfirmed,
    resend_verification_request,
    user_status,
    status_code,
    snapshot,
):
    email = {
        "not_found": user_email_not_found,
        "unconfirmed": user_email_unconfirmed,
        "confirmed": user_email,
    }[user_status]
    resend_verification_request = resend_verification_request(email=email)
    api_response = api_request(
        api_host,
        "post",
        "v1/users/resend-verification",
        json=resend_verification_request,
    )
    api_assert_match(api_response, status_code, snapshot)


@pytest.mark.aws
@pytest.mark.parametrize(
    "user_status, verification_code_is_correct, status_code",
    [
        ("not_found", True, 400),
        ("confirmed", True, 200),
        ("confirmed", False, 200),
        ("unconfirmed", False, 400),
        ("unconfirmed", True, 200),
    ],
)
def test_confirm_signup(
    api_host,
    users_api_service,
    user_email_not_found,
    user_email_unconfirmed,
    user_email,
    user,
    user_unconfirmed,
    confirm_signup_request,
    user_status,
    verification_code_is_correct,
    status_code,
    snapshot,
):
    if user_status == "unconfirmed" and verification_code_is_correct:
        msg = "Unclear how to mock the reception of email verification code."
        pytest.xfail(msg)

    email = {
        "not_found": user_email_not_found,
        "unconfirmed": user_email_unconfirmed,
        "confirmed": user_email,
    }[user_status]

    confirm_signup_request = confirm_signup_request(email=email)
    api_response = api_request(
        api_host, "post", "v1/users/confirm-signup", json=confirm_signup_request,
    )
    api_assert_match(api_response, status_code, snapshot)


@pytest.mark.aws
@pytest.mark.parametrize(
    "user_status, status_code",
    [("not_found", 400), ("unconfirmed", 400), ("confirmed", 200)],
)
def test_forgot_password(
    api_host,
    users_api_service,
    user_email_not_found,
    user_email_unconfirmed,
    user_email,
    user,
    user_unconfirmed,
    forgot_password_request,
    user_status,
    status_code,
    snapshot,
):
    email = {
        "not_found": user_email_not_found,
        "unconfirmed": user_email_unconfirmed,
        "confirmed": user_email,
    }[user_status]
    forgot_password_request = forgot_password_request(email=email)
    api_response = api_request(
        api_host, "post", "v1/users/forgot-password", json=forgot_password_request,
    )
    api_assert_match(api_response, status_code, snapshot)


@pytest.mark.aws
@pytest.mark.parametrize(
    "user_status, verification_code_is_correct, status_code",
    [
        ("not_found", True, 400),
        ("unconfirmed", True, 400),
        ("confirmed", True, 400),
        ("forgot_password", False, 400),
        ("forgot_password", True, 200),
    ],
)
def test_reset_password(
    api_host,
    users_api_service,
    user_email_not_found,
    user_email_unconfirmed,
    user_email,
    user_new_password,
    user_verification_code,
    user_unconfirmed,
    user,
    reset_password_request,
    user_status,
    verification_code_is_correct,
    status_code,
    user_pool_client_id,
    snapshot,
):
    if (user_status == "forgot_password") and verification_code_is_correct:
        msg = "Unclear how to mock the reception of email verification code."
        pytest.xfail(msg)

    if user_status == "forgot_password":
        cognito = boto3.client("cognito-idp")
        cognito.forgot_password(
            ClientId=user_pool_client_id, Username=user_email,
        )
        time.sleep(0.5)

    email = {
        "not_found": user_email_not_found,
        "unconfirmed": user_email_unconfirmed,
        "confirmed": user_email,
        "forgot_password": user_email,
    }[user_status]
    new_password = user_new_password
    verification_code = (
        user_verification_code if verification_code_is_correct else "foobar"
    )
    reset_password_request = reset_password_request(
        email=email, new_password=new_password, verification_code=verification_code
    )
    api_response = api_request(
        api_host, "post", "v1/users/reset-password", json=reset_password_request,
    )
    api_assert_match(api_response, status_code, snapshot)


# ----------------------------------- Authenticate ----------------------------------- #
@pytest.mark.aws
@pytest.mark.parametrize(
    "user_status, password_is_correct, status_code",
    [
        ("not_found", False, 401),
        ("unconfirmed", False, 400),
        ("confirmed", False, 401),
        ("confirmed", True, 200),
    ],
)
def test_authenticate(
    stage,
    user_email_not_found,
    user_email_unconfirmed,
    user_email,
    user_password,
    user_unconfirmed,
    user,
    users_api_service,
    authenticate_event,
    user_status,
    password_is_correct,
    status_code,
    snapshot,
):
    email = {
        "not_found": user_email_not_found,
        "unconfirmed": user_email_unconfirmed,
        "confirmed": user_email,
    }[user_status]
    password = user_password if password_is_correct else "foo"
    authenticate_event = authenticate_event(email=email, password=password)
    handler_response = sls_invoke(stage, "authenticate", authenticate_event)
    msg = f"Authentication failed:\n" f"{handler_response.stdout.decode('utf-8')}"
    handler_assert_match(handler_response, stage, msg, status_code, snapshot)


# -------------------------------------- Profile ------------------------------------- #
@pytest.mark.aws
def test_profile(
    stage, users_api_service, profile_event, snapshot,
):
    status_code = 200
    profile_event = profile_event()
    handler_response = sls_invoke(stage, "profile", profile_event)
    msg = f"Getting profile failed:\n" f"{handler_response.stdout.decode('utf-8')}"
    handler_assert_match(handler_response, stage, msg, status_code, snapshot)
