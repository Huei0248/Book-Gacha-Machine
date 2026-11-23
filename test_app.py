"""以 mock 驗證抽書流程，不連線至 Open Library。"""
import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from api import index as book_app


def setup_function():
    book_app.app.config["TESTING"] = True
    book_app._cache.clear()


def test_draw_returns_randomly_selected_api_book(monkeypatch):
    books = [
        {"key": "/works/OL1W", "title": "雲端旅人", "authors": [{"name": "林作者"}], "subject": ["冒險", "旅行"], "cover_id": 42, "first_publish_year": 2020},
        {"key": "/works/OL2W", "title": "星海", "authors": []},
    ]
    monkeypatch.setattr(book_app, "get_subject_books", lambda subject: books)
    monkeypatch.setattr(book_app.random, "choice", lambda options: options[0])
    response = book_app.app.test_client().post("/api/draw", json={"subject": "travel"})
    assert response.status_code == 200
    assert response.json["book"]["title"] == "雲端旅人"
    assert response.json["book"]["cover_url"].endswith("/42-L.jpg")
    assert len(response.json["book"]["subjects"]) <= 3


def test_open_library_request_has_user_agent_and_timeout(monkeypatch):
    response = Mock()
    response.json.return_value = {"works": []}
    monkeypatch.setattr(book_app.requests, "get", Mock(return_value=response))
    book_app.get_subject_books("travel")
    args, kwargs = book_app.requests.get.call_args
    assert args[0] == "https://openlibrary.org/subjects/travel.json"
    assert kwargs["params"] == {"limit": 30}
    assert kwargs["headers"]["User-Agent"].startswith("BookGachaMachine/1.0 (")
    assert kwargs["timeout"] == 5


def test_upstream_failure_returns_friendly_message(monkeypatch):
    monkeypatch.setattr(book_app, "get_subject_books", Mock(side_effect=book_app.requests.Timeout()))
    response = book_app.app.test_client().post("/api/draw", json={"subject": "mystery"})
    assert response.status_code == 502
    assert "請稍後再試" in response.json["error"]


def test_empty_subject_returns_friendly_message(monkeypatch):
    monkeypatch.setattr(book_app, "get_subject_books", lambda subject: [])
    response = book_app.app.test_client().post("/api/draw", json={"subject": "history"})
    assert response.status_code == 404
    assert "暫時沒有找到書籍" in response.json["error"]


def test_invalid_subject_is_rejected():
    response = book_app.app.test_client().post("/api/draw", json={"subject": "invented_subject"})
    assert response.status_code == 400


def test_home_route_renders_subjects():
    response = book_app.app.test_client().get("/")
    assert response.status_code == 200
    assert "靈感選書扭蛋機" in response.get_data(as_text=True)
