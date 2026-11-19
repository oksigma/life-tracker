from datetime import date, timedelta
from io import BytesIO
from typing import Any

import pillow_heif
import pytest
from fastapi.testclient import TestClient
from PIL import ExifTags, Image
from pymongo.database import Database

TODAY = date.today().isoformat()
URL = "/api/clothing/outfits"


def make_image(
    fmt: str = "JPEG",
    size: tuple[int, int] = (300, 200),
    mode: str = "RGB",
    orientation: int | None = None,
    gps: bool = False,
) -> bytes:
    image = Image.new(mode, size, (200, 50, 50, 128) if mode == "RGBA" else (200, 50, 50))
    exif = Image.Exif()
    if orientation:
        exif[ExifTags.Base.Orientation] = orientation
    if gps:
        exif[ExifTags.Base.Make] = "TestCam"
        gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
        gps_ifd[ExifTags.GPS.GPSLatitudeRef] = "N"
        gps_ifd[ExifTags.GPS.GPSLatitude] = (51.0, 30.0, 0.0)
        gps_ifd[ExifTags.GPS.GPSLongitudeRef] = "W"
        gps_ifd[ExifTags.GPS.GPSLongitude] = (0.0, 7.0, 0.0)
    buffer = BytesIO()
    image.save(buffer, format=fmt, **({"exif": exif.tobytes()} if len(exif) else {}))
    return buffer.getvalue()


def upload(
    client: TestClient,
    photo: bytes | None = None,
    filename: str = "outfit.jpg",
    **form: str,
) -> Any:
    return client.post(
        URL,
        files={"photo": (filename, photo if photo is not None else make_image(), "image/jpeg")},
        data=form,
    )


def create(client: TestClient, **form: str) -> dict[str, Any]:
    response = upload(client, **form)
    assert response.status_code == 201, response.text
    return response.json()


def stored_image(client: TestClient, url: str) -> Image.Image:
    response = client.get(url)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    image = Image.open(BytesIO(response.content))
    image.load()
    return image


def photo_file_count(db: Database) -> int:
    return db["outfit_photos.files"].count_documents({})


def test_list_is_empty_initially(client: TestClient) -> None:
    assert client.get(URL).json() == {"items": [], "total": 0}


def test_upload_defaults_to_today(client: TestClient) -> None:
    outfit = create(client)
    assert outfit["worn_on"] == TODAY
    assert outfit["notes"] is None
    assert outfit["photo_url"] == f"{URL}/{outfit['id']}/photo"
    assert outfit["thumbnail_url"] == f"{URL}/{outfit['id']}/thumbnail"


def test_upload_with_chosen_date_and_notes(client: TestClient) -> None:
    outfit = create(client, worn_on="2026-03-10", notes="  Wedding  ")
    assert outfit["worn_on"] == "2026-03-10"
    assert outfit["notes"] == "Wedding"


def test_upload_rejects_future_date(client: TestClient, db: Database) -> None:
    future = (date.today() + timedelta(days=3)).isoformat()
    assert upload(client, worn_on=future).status_code == 422
    assert client.get(URL).json()["total"] == 0
    assert photo_file_count(db) == 0


def test_upload_rejects_long_notes(client: TestClient) -> None:
    assert upload(client, notes="x" * 1001).status_code == 422


def test_upload_requires_photo(client: TestClient) -> None:
    assert client.post(URL, data={"worn_on": TODAY}).status_code == 422


def test_rejects_non_image(client: TestClient, db: Database) -> None:
    response = upload(client, photo=b"%PDF-1.7 not an image", filename="doc.pdf")
    assert response.status_code == 415
    assert "JPEG" in response.json()["detail"]
    assert client.get(URL).json()["total"] == 0
    assert photo_file_count(db) == 0


def test_rejects_unsupported_image_format(client: TestClient) -> None:
    assert upload(client, photo=make_image("GIF"), filename="a.gif").status_code == 415


def test_rejects_too_large(client: TestClient, db: Database) -> None:
    response = upload(client, photo=b"\0" * (15 * 1024 * 1024 + 1))
    assert response.status_code == 413
    assert photo_file_count(db) == 0


def test_strips_all_metadata_including_gps(client: TestClient) -> None:
    original = make_image(gps=True)
    assert Image.open(BytesIO(original)).getexif().get_ifd(ExifTags.IFD.GPSInfo)
    outfit = upload(client, photo=original).json()
    for url in (outfit["photo_url"], outfit["thumbnail_url"]):
        image = stored_image(client, url)
        assert len(image.getexif()) == 0
        assert "exif" not in image.info
        assert "icc_profile" not in image.info


def test_rotates_photo_upright(client: TestClient) -> None:
    # Orientation 6 = camera held sideways; a 300x200 sensor image should display as 200x300.
    outfit = upload(client, photo=make_image(size=(300, 200), orientation=6)).json()
    assert stored_image(client, outfit["photo_url"]).size == (200, 300)


def test_resizes_large_photo_and_makes_thumbnail(client: TestClient) -> None:
    outfit = upload(client, photo=make_image(size=(3000, 1500))).json()
    assert stored_image(client, outfit["photo_url"]).size == (2000, 1000)
    assert stored_image(client, outfit["thumbnail_url"]).size == (400, 200)


def test_small_photo_is_not_enlarged(client: TestClient) -> None:
    outfit = upload(client, photo=make_image(size=(300, 200))).json()
    assert stored_image(client, outfit["photo_url"]).size == (300, 200)


@pytest.mark.parametrize(("fmt", "mode"), [("PNG", "RGBA"), ("WEBP", "RGB"), ("PNG", "P")])
def test_accepts_png_and_webp(client: TestClient, fmt: str, mode: str) -> None:
    response = upload(client, photo=make_image(fmt, mode=mode), filename=f"a.{fmt.lower()}")
    assert response.status_code == 201, response.text
    assert stored_image(client, response.json()["photo_url"]).mode == "RGB"


def test_accepts_heic(client: TestClient) -> None:
    image = Image.new("RGB", (320, 240), (10, 120, 200))
    buffer = BytesIO()
    try:
        pillow_heif.from_pillow(image).save(buffer, format="HEIF")
    except Exception as exc:  # pragma: no cover - depends on the platform's HEIF encoder
        pytest.skip(f"HEIF encoder unavailable: {exc}")
    response = upload(client, photo=buffer.getvalue(), filename="IMG_0001.HEIC")
    assert response.status_code == 201, response.text
    assert stored_image(client, response.json()["photo_url"]).size == (320, 240)


def test_list_is_newest_day_first(client: TestClient) -> None:
    create(client, worn_on="2025-01-01")
    create(client, worn_on=TODAY)
    create(client, worn_on="2026-02-02")
    days = [o["worn_on"] for o in client.get(URL).json()["items"]]
    assert days == [TODAY, "2026-02-02", "2025-01-01"]


def test_multiple_outfits_per_day(client: TestClient) -> None:
    first = create(client, notes="Day")
    second = create(client, notes="Evening")
    items = client.get(URL).json()["items"]
    assert [o["id"] for o in items] == [second["id"], first["id"]]


def test_pagination(client: TestClient) -> None:
    for day in range(1, 5):
        create(client, worn_on=f"2026-01-0{day}")
    body = client.get(URL, params={"limit": 2, "offset": 1}).json()
    assert body["total"] == 4
    assert [o["worn_on"] for o in body["items"]] == ["2026-01-03", "2026-01-02"]


def test_change_date(client: TestClient) -> None:
    outfit = create(client)
    response = client.patch(f"{URL}/{outfit['id']}", json={"worn_on": "2026-05-20"})
    assert response.status_code == 200
    assert response.json()["worn_on"] == "2026-05-20"
    assert response.json()["photo_url"] == outfit["photo_url"]
    assert client.get(f"{URL}/{outfit['id']}").json()["worn_on"] == "2026-05-20"


def test_update_notes_and_clear_them(client: TestClient) -> None:
    outfit = create(client, notes="Old")
    assert client.patch(f"{URL}/{outfit['id']}", json={"notes": "New"}).json()["notes"] == "New"
    assert client.patch(f"{URL}/{outfit['id']}", json={"notes": None}).json()["notes"] is None


@pytest.mark.parametrize(
    "body",
    [
        {"worn_on": None},
        {"worn_on": (date.today() + timedelta(days=3)).isoformat()},
        {"notes": "x" * 1001},
    ],
)
def test_update_rejects_invalid(client: TestClient, body: dict[str, Any]) -> None:
    outfit = create(client)
    assert client.patch(f"{URL}/{outfit['id']}", json=body).status_code == 422


def test_delete_removes_record_and_photos(client: TestClient, db: Database) -> None:
    outfit = create(client)
    assert photo_file_count(db) == 2
    assert client.delete(f"{URL}/{outfit['id']}").status_code == 204
    assert client.get(f"{URL}/{outfit['id']}").status_code == 404
    assert client.get(outfit["photo_url"]).status_code == 404
    assert photo_file_count(db) == 0
    assert db["outfit_photos.chunks"].count_documents({}) == 0


@pytest.mark.parametrize("outfit_id", ["not-an-id", "507f1f77bcf86cd799439011"])
def test_missing_or_invalid_id_returns_404(client: TestClient, outfit_id: str) -> None:
    assert client.get(f"{URL}/{outfit_id}").status_code == 404
    assert client.get(f"{URL}/{outfit_id}/photo").status_code == 404
    assert client.get(f"{URL}/{outfit_id}/thumbnail").status_code == 404
    assert client.patch(f"{URL}/{outfit_id}", json={"notes": "x"}).status_code == 404
    assert client.delete(f"{URL}/{outfit_id}").status_code == 404


def test_photos_are_cacheable(client: TestClient) -> None:
    outfit = create(client)
    response = client.get(outfit["thumbnail_url"])
    assert "immutable" in response.headers["cache-control"]
