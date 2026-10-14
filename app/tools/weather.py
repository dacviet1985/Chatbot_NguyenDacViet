from __future__ import annotations

import logging
import re
from urllib.parse import quote

import requests

from app.tools.calculator import ToolResult

logger = logging.getLogger(__name__)

_WEATHER_CODE_MAP = {
    0: "trời quang",
    1: "ít mây",
    2: "mây rải rác",
    3: "nhiều mây",
    45: "sương mù",
    48: "sương mù đóng băng",
    51: "mưa phùn nhẹ",
    53: "mưa phùn vừa",
    55: "mưa phùn dày",
    56: "mưa phùn lạnh nhẹ",
    57: "mưa phùn lạnh mạnh",
    61: "mưa nhẹ",
    63: "mưa vừa",
    65: "mưa to",
    66: "mưa lạnh nhẹ",
    67: "mưa lạnh mạnh",
    71: "tuyết nhẹ",
    73: "tuyết vừa",
    75: "tuyết dày",
    77: "hạt tuyết",
    80: "mưa rào nhẹ",
    81: "mưa rào vừa",
    82: "mưa rào mạnh",
    85: "mưa tuyết nhẹ",
    86: "mưa tuyết mạnh",
    95: "dông",
    96: "dông có mưa đá nhẹ",
    99: "dông có mưa đá mạnh",
}


class WeatherTool:
    """Fetches current weather using Open-Meteo geocoding and forecast APIs."""

    name = "weather"
    _WEATHER_TERMS = (
        "thời tiết",
        "weather",
        "nhiệt độ",
        "độ ẩm",
        "gió",
        "mưa",
        "nắng",
        "trời",
    )
    _FILLER_PHRASES = (
        "ý tôi là",
        "y toi la",
        "cho tôi biết",
        "cho mình biết",
        "cho tôi",
        "cho mình",
        "giúp tôi",
        "giúp mình",
        "xem giúp",
        "xem hộ",
        "xem",
        "tìm giúp",
        "tìm",
        "dự báo",
        "hôm nay",
        "ngày mai",
        "bây giờ",
        "hiện tại",
        "lúc này",
        "ra sao",
        "thế nào",
        "như nào",
        "sao rồi",
        "sao",
        "không",
        "vậy",
        "ạ",
        "nhé",
        "nha",
    )

    def __init__(self, timeout_seconds: float = 30.0) -> None:
        self.timeout_seconds = timeout_seconds

    def can_handle(self, text: str) -> bool:
        normalized = text.lower().strip()
        if not normalized:
            return False
        return any(keyword in normalized for keyword in self._WEATHER_TERMS)

    def run(self, text: str) -> ToolResult:
        location = self.extract_location(text)
        if not location:
            raise ValueError("Không xác định được địa điểm để tra cứu thời tiết.")
        geo = self._geocode(location)
        weather = self._forecast(geo["latitude"], geo["longitude"])
        answer = self._format_answer(geo, weather)
        logger.info("[TOOL] weather | input=%s | result=%s", location, answer)
        return ToolResult(
            name=self.name,
            input_text=location,
            output_text=answer,
            sources=[{"source": "open-meteo.com", "page": None}],
        )

    def extract_location(self, text: str) -> str:
        cleaned = text.lower().strip()
        replacements = {
            "ở": " ",
            "tại": " ",
            "khu vực": " ",
            "thành phố": " ",
        }
        for keyword in self._WEATHER_TERMS:
            cleaned = cleaned.replace(keyword, " ")
        for phrase in self._FILLER_PHRASES:
            cleaned = cleaned.replace(phrase, " ")
        for source, target in replacements.items():
            cleaned = cleaned.replace(source, target)
        cleaned = re.sub(r"\b(của|về|giùm|dum|voi|với|tai|o)\b", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.?!")
        cleaned = re.sub(r"\b(bao nhiêu độ|bao nhieu do|mấy độ|may do)\b", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.?!")
        return cleaned.title()

    def _geocode(self, location: str) -> dict[str, object]:
        url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            f"name={quote(location)}&count=1&language=vi&format=json"
        )
        response = requests.get(url, timeout=self.timeout_seconds)
        response.raise_for_status()
        data = response.json()
        results = data.get("results") or []
        if not results:
            raise ValueError(f"Không tìm thấy địa điểm '{location}'.")
        item = results[0]
        return {
            "name": item.get("name", location),
            "country": item.get("country", ""),
            "admin1": item.get("admin1", ""),
            "latitude": item["latitude"],
            "longitude": item["longitude"],
        }

    def _forecast(self, latitude: float, longitude: float) -> dict[str, object]:
        url = (
            "https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}"
            "&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            "&timezone=auto&forecast_days=1"
        )
        response = requests.get(url, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()

    def _format_answer(self, geo: dict[str, object], weather: dict[str, object]) -> str:
        current = weather.get("current", {})
        daily = weather.get("daily", {})
        weather_code = int(current.get("weather_code", 0))
        description = _WEATHER_CODE_MAP.get(weather_code, "không xác định")
        city = str(geo.get("name", "Địa điểm chưa rõ"))
        admin1 = str(geo.get("admin1", "")).strip()
        country = str(geo.get("country", "")).strip()
        place = ", ".join(part for part in [city, admin1, country] if part)
        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")
        temp_max = self._first(daily.get("temperature_2m_max"))
        temp_min = self._first(daily.get("temperature_2m_min"))
        rain = self._first(daily.get("precipitation_probability_max"))
        return (
            f"Thời tiết hiện tại tại {place}: {description}, nhiệt độ {temp}°C, độ ẩm {humidity}%, "
            f"gió {wind} km/h. Hôm nay nhiệt độ dao động từ {temp_min}°C đến {temp_max}°C, "
            f"xác suất mưa tối đa {rain}%."
        )

    def _first(self, value: object) -> object:
        if isinstance(value, list) and value:
            return value[0]
        return value