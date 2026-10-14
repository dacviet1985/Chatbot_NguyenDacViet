from __future__ import annotations

from app.tools.weather import WeatherTool


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_weather_tool_formats_result(monkeypatch):
    tool = WeatherTool(timeout_seconds=1)

    payloads = [
        {
            "results": [
                {
                    "name": "Hà Nội",
                    "country": "Việt Nam",
                    "admin1": "Hà Nội",
                    "latitude": 21.0245,
                    "longitude": 105.8412,
                }
            ]
        },
        {
            "current": {
                "temperature_2m": 29.1,
                "relative_humidity_2m": 70,
                "weather_code": 1,
                "wind_speed_10m": 8.5,
            },
            "daily": {
                "temperature_2m_max": [32.0],
                "temperature_2m_min": [25.0],
                "precipitation_probability_max": [20],
            },
        },
    ]

    def fake_get(url, timeout):
        return DummyResponse(payloads.pop(0))

    monkeypatch.setattr("app.tools.weather.requests.get", fake_get)
    result = tool.run("thời tiết hà nội hôm nay")

    assert result.name == "weather"
    assert "Hà Nội" in result.output_text
    assert result.sources == [{"source": "open-meteo.com", "page": None}]


def test_weather_tool_detection_and_location_extraction():
    tool = WeatherTool(timeout_seconds=1)

    assert tool.can_handle("thời tiết hà nội hôm nay") is True
    assert tool.extract_location("tìm thời tiết hà nội hôm nay") == "Hà Nội"
    assert tool.extract_location("ý tôi là xem thời tiết hà nội hôm nay ra sao") == "Hà Nội"


def test_weather_tool_missing_location_after_cleanup():
    tool = WeatherTool(timeout_seconds=1)

    assert tool.extract_location("thời tiết hôm nay thế nào") == ""