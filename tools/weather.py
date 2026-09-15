# -*- coding: utf-8 -*-
"""Open-Meteo 真实天气 Tool（免 API Key）：实时 + 未来几天预报。"""
from __future__ import annotations

import httpx
from langchain.tools import tool

_WEATHER_CODE_ZH = {
    0: "晴",
    1: "主要晴朗",
    2: "局部多云",
    3: "阴天",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "大毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    80: "小阵雨",
    81: "阵雨",
    82: "强阵雨",
    95: "雷阵雨",
}


def _code_zh(code) -> str:
    return _WEATHER_CODE_ZH.get(code, f"天气码{code}")


@tool
def get_weather(city: str, days: int = 7) -> str:
    """查询指定城市的实时天气，以及未来若干天的预报（最高/最低温、天气状况）。

    Args:
        city: 城市名称，如「北京」「上海」
        days: 预报天数，1～7，默认 7；问「明天」「这周」时用此工具并设合适天数
    """
    city = (city or "").strip()
    if not city:
        return "请提供城市名称，例如：北京"

    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 7
    days = max(1, min(days, 7))

    try:
        geo = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "zh"},
            timeout=10.0,
        )
        geo.raise_for_status()
        results = geo.json().get("results") or []
        if not results:
            return f"找不到城市：{city}"

        loc = results[0]
        lat, lon = loc["latitude"], loc["longitude"]
        name = loc.get("name", city)

        weather_resp = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "temperature_2m,relative_humidity_2m,"
                    "weather_code,wind_speed_10m"
                ),
                "daily": (
                    "weather_code,temperature_2m_max,"
                    "temperature_2m_min,precipitation_probability_max"
                ),
                "forecast_days": days,
                "timezone": "Asia/Shanghai",
            },
            timeout=10.0,
        )
        weather_resp.raise_for_status()
        data = weather_resp.json()
        cur = data["current"]
        daily = data.get("daily") or {}

        lines = [
            (
                f"{name}实时天气：{_code_zh(cur.get('weather_code'))}；"
                f"气温 {cur.get('temperature_2m')}°C；"
                f"湿度 {cur.get('relative_humidity_2m')}%；"
                f"风速 {cur.get('wind_speed_10m')} km/h"
            ),
            f"未来 {days} 天预报：",
        ]

        dates = daily.get("time") or []
        codes = daily.get("weather_code") or []
        tmax = daily.get("temperature_2m_max") or []
        tmin = daily.get("temperature_2m_min") or []
        precip = daily.get("precipitation_probability_max") or []

        for i, date in enumerate(dates):
            code = codes[i] if i < len(codes) else None
            hi = tmax[i] if i < len(tmax) else "?"
            lo = tmin[i] if i < len(tmin) else "?"
            rain = precip[i] if i < len(precip) else "?"
            lines.append(
                f"- {date} {_code_zh(code)}；"
                f"{lo}～{hi}°C；降水概率 {rain}%"
            )

        lines.append("（数据来源：Open-Meteo）")
        return "\n".join(lines)
    except httpx.HTTPError as e:
        return f"天气查询失败（网络/接口错误）：{e}"
    except Exception as e:
        return f"天气查询失败：{e}"
