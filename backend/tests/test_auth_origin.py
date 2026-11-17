import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.v1.endpoints.auth import check_origin


def make_request(origin, host):
    headers = [(b"host", host.encode())]
    if origin is not None:
        headers.append((b"origin", origin.encode()))
    return Request({"type": "http", "headers": headers})


@pytest.mark.parametrize(
    "origin, host",
    [
        (None, "localhost:5173"),  # client non navigateur
        ("http://localhost:5173", "localhost:5173"),  # liste CORS
        ("http://192.168.1.20:5173", "192.168.1.20:5173"),  # autre machine du Wi-Fi
        ("http://ec2-1-2-3-4.compute.amazonaws.com", "ec2-1-2-3-4.compute.amazonaws.com"),
    ],
)
def test_same_site_is_accepted(origin, host):
    check_origin(make_request(origin, host))


def test_foreign_site_is_rejected():
    with pytest.raises(HTTPException) as error:
        check_origin(make_request("http://evil.example", "192.168.1.20:5173"))
    assert error.value.status_code == 403
