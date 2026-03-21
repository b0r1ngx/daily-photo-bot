"""Unit tests for PhotoService."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.service.photo_service import PhotoService
from src.types.exceptions import PhotoNotFoundError
from src.types.photo import PhotoResult

# Import extraction helpers for direct unit testing
from src.service.photo_service import _extract_camera, _extract_description, _extract_location


@pytest.fixture
def sent_repo():
    repo = AsyncMock()
    repo.count_by_topic.return_value = 0
    repo.get_sent_ids.return_value = set()
    return repo


@pytest.fixture
def service(sent_repo):
    return PhotoService(sent_photo_repo=sent_repo)


def _make_pexels_response(photos: list[dict] | None = None):
    """Create a mock Pexels API response."""
    if photos is None:
        photos = [
            {
                "id": 123,
                "src": {"large": "https://images.pexels.com/123.jpg"},
                "photographer": "Test Photographer",
                "url": "https://pexels.com/photo/123",
                "alt": "A parrot",
            }
        ]
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"photos": photos}
    return mock_resp


def _make_pexels_rate_limit_response():
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {"Retry-After": "60"}
    return mock_resp


@pytest.mark.asyncio
async def test_get_photo_from_pexels(service: PhotoService, sent_repo):
    mock_resp = _make_pexels_response()
    with patch("src.service.photo_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = await service.get_photo("parrots", topic_id=1)

    assert isinstance(result, PhotoResult)
    assert result.source == "pexels"
    assert result.photo_id == "123"
    sent_repo.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_photo_pexels_rate_limit_falls_back_to_unsplash(service: PhotoService):
    pexels_resp = _make_pexels_rate_limit_response()
    unsplash_resp = MagicMock()
    unsplash_resp.status_code = 200
    unsplash_resp.json.return_value = [
        {
            "id": "abc",
            "urls": {"regular": "https://images.unsplash.com/abc.jpg"},
            "user": {"name": "Unsplash Photographer"},
            "links": {
                "html": "https://unsplash.com/photos/abc",
                "download_location": "https://api.unsplash.com/photos/abc/download",
            },
            "alt_description": "A parrot",
        }
    ]

    # Track download response
    download_resp = MagicMock()
    download_resp.status_code = 200

    async def mock_get(*args, **kwargs):
        url = args[0] if args else kwargs.get("url", "")
        if "pexels" in str(url):
            return pexels_resp
        if "unsplash.com/photos/random" in str(url):
            return unsplash_resp
        # Download tracking call
        return download_resp

    with (
        patch("src.service.photo_service.httpx.AsyncClient") as mock_client_cls,
        patch("src.service.photo_service.UNSPLASH_ACCESS_KEY", "test-unsplash-key"),
    ):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = mock_get
        mock_client_cls.return_value = mock_client

        result = await service.get_photo("parrots", topic_id=1)

    assert result.source == "unsplash"


@pytest.mark.asyncio
async def test_get_photo_both_fail_raises(service: PhotoService):
    mock_resp = MagicMock()
    mock_resp.status_code = 500

    with patch("src.service.photo_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        with pytest.raises(PhotoNotFoundError):
            await service.get_photo("nonexistent_xyz", topic_id=1)


@pytest.mark.asyncio
async def test_get_photo_skips_already_sent(service: PhotoService, sent_repo):
    sent_repo.get_sent_ids.return_value = {"123"}
    photos = [
        {
            "id": 123,
            "src": {"large": "https://images.pexels.com/123.jpg"},
            "photographer": "P1",
            "url": "https://pexels.com/photo/123",
            "alt": "A",
        },
        {
            "id": 456,
            "src": {"large": "https://images.pexels.com/456.jpg"},
            "photographer": "P2",
            "url": "https://pexels.com/photo/456",
            "alt": "B",
        },
    ]
    mock_resp = _make_pexels_response(photos)

    with patch("src.service.photo_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = await service.get_photo("parrots", topic_id=1)

    assert result.photo_id == "456"


@pytest.mark.asyncio
async def test_api_request_recorded_on_pexels_call(sent_repo):
    """Verify record_api_request('pexels') is called after Pexels API call."""
    recorder = AsyncMock()
    svc = PhotoService(sent_photo_repo=sent_repo, api_request_recorder=recorder)
    mock_resp = _make_pexels_response()

    with patch("src.service.photo_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        await svc.get_photo("parrots", topic_id=1)

    recorder.record_api_request.assert_any_await("pexels")


@pytest.mark.asyncio
async def test_api_request_recorded_on_unsplash_fallback(sent_repo):
    """Verify both pexels and unsplash requests are recorded on fallback."""
    recorder = AsyncMock()
    svc = PhotoService(sent_photo_repo=sent_repo, api_request_recorder=recorder)

    pexels_resp = _make_pexels_rate_limit_response()
    unsplash_resp = MagicMock()
    unsplash_resp.status_code = 200
    unsplash_resp.json.return_value = [
        {
            "id": "abc",
            "urls": {"regular": "https://images.unsplash.com/abc.jpg"},
            "user": {"name": "Unsplash Photographer"},
            "links": {
                "html": "https://unsplash.com/photos/abc",
                "download_location": "https://api.unsplash.com/photos/abc/download",
            },
            "alt_description": "A parrot",
        }
    ]
    download_resp = MagicMock()
    download_resp.status_code = 200

    async def mock_get(*args, **kwargs):
        url = args[0] if args else kwargs.get("url", "")
        if "pexels" in str(url):
            return pexels_resp
        if "unsplash.com/photos/random" in str(url):
            return unsplash_resp
        return download_resp

    with (
        patch("src.service.photo_service.httpx.AsyncClient") as mock_client_cls,
        patch("src.service.photo_service.UNSPLASH_ACCESS_KEY", "test-unsplash-key"),
    ):
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = mock_get
        mock_client_cls.return_value = mock_client

        await svc.get_photo("parrots", topic_id=1)

    recorder.record_api_request.assert_any_await("pexels")
    recorder.record_api_request.assert_any_await("unsplash")


@pytest.mark.asyncio
async def test_no_recorder_does_not_crash(sent_repo):
    """Verify PhotoService works fine when api_request_recorder is None."""
    svc = PhotoService(sent_photo_repo=sent_repo, api_request_recorder=None)
    mock_resp = _make_pexels_response()

    with patch("src.service.photo_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = await svc.get_photo("parrots", topic_id=1)

    assert isinstance(result, PhotoResult)
    assert result.source == "pexels"


@pytest.mark.asyncio
async def test_exhaustion_reset(service: PhotoService, sent_repo):
    sent_repo.count_by_topic.return_value = 501  # > threshold
    sent_repo.get_sent_ids.return_value = set()
    mock_resp = _make_pexels_response()

    with patch("src.service.photo_service.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        await service.get_photo("parrots", topic_id=1)

    sent_repo.reset_by_topic.assert_awaited_once_with(1)


# --- Metadata extraction tests ---


def test_extract_description_full():
    """Extract description from Unsplash photo with both description and alt."""
    photo = {"description": "A beautiful sunset", "alt_description": "sunset colors"}
    assert _extract_description(photo) == "A beautiful sunset"


def test_extract_description_fallback_to_alt():
    """Falls back to alt_description when description is empty."""
    photo = {"description": "", "alt_description": "sunset colors"}
    assert _extract_description(photo) == "sunset colors"


def test_extract_description_missing():
    """Returns empty string when both fields are missing."""
    assert _extract_description({}) == ""


def test_extract_location_from_name():
    """Extract location from the 'name' field."""
    photo = {"location": {"name": "Montreal, Canada", "city": "Montreal", "country": "Canada"}}
    assert _extract_location(photo) == "Montreal, Canada"


def test_extract_location_fallback_city_country():
    """Falls back to city+country when name is missing."""
    photo = {"location": {"name": None, "city": "Tokyo", "country": "Japan"}}
    assert _extract_location(photo) == "Tokyo, Japan"


def test_extract_location_missing():
    """Returns empty string when location is not present."""
    assert _extract_location({}) == ""


def test_extract_camera_from_name():
    """Extract camera from exif 'name' field."""
    photo = {"exif": {"name": "Canon, EOS 40D", "make": "Canon", "model": "EOS 40D"}}
    assert _extract_camera(photo) == "Canon, EOS 40D"


def test_extract_camera_fallback_make_model():
    """Falls back to make+model when name is missing."""
    photo = {"exif": {"name": None, "make": "Nikon", "model": "D750"}}
    assert _extract_camera(photo) == "Nikon, D750"


def test_extract_camera_missing():
    """Returns empty string when exif is not present."""
    assert _extract_camera({}) == ""


def test_extract_description_truncation():
    """Long descriptions are truncated to 100 chars."""
    long_desc = "A" * 150
    photo = {"description": long_desc}
    result = _extract_description(photo)
    assert len(result) == 100
    assert result.endswith("...")
