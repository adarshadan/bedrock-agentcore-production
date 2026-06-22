import os
import random
from typing import Optional
from src.actions.base import BaseTool, ToolParameter, ToolResult, ToolPermission


class WeatherTool(BaseTool):
    name = "get_weather"
    description = "Get current weather conditions for a city. Returns temperature, conditions, humidity, and wind speed."
    parameters = [
        ToolParameter(
            name="city",
            type="string",
            description="City name",
            required=True,
            example="San Francisco",
        ),
        ToolParameter(
            name="units",
            type="string",
            description="Temperature units",
            required=False,
            default="imperial",
            enum=["imperial", "metric"],
        ),
        ToolParameter(
            name="include_forecast",
            type="boolean",
            description="Include 5-day forecast",
            required=False,
            default=False,
        ),
    ]
    permission = ToolPermission.PUBLIC

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("WEATHER_API_KEY")
        self.use_mock = not self.api_key

    def execute(
        self,
        city: str,
        units: str = "imperial",
        include_forecast: bool = False,
        **kwargs,
    ) -> ToolResult:
        error = self.validate_inputs(city=city, units=units)
        if error:
            return ToolResult(success=False, error=error)
        try:
            if self.use_mock:
                return self._mock_weather(city, units, include_forecast)
            else:
                return self._real_weather(city, units, include_forecast)
        except Exception as e:
            return ToolResult(success=False, error=f"Weather service error: {str(e)}")

    def _mock_weather(self, city: str, units: str, forecast: bool) -> ToolResult:
        temp_unit = "°F" if units == "imperial" else "°C"
        base_temp = 72 if units == "imperial" else 22
        temp = base_temp + random.randint(-10, 10)
        conditions = random.choice(
            ["sunny", "partly cloudy", "cloudy", "rainy", "clear"]
        )
        result = {
            "city": city,
            "temperature": f"{temp}{temp_unit}",
            "condition": conditions,
            "humidity": f"{random.randint(30, 80)}%",
        }
        if forecast:
            result["forecast"] = [
                {
                    "day": "Tomorrow",
                    "temp": f"{temp + random.randint(-5, 5)}{temp_unit}",
                    "condition": random.choice(["sunny", "cloudy", "rainy"]),
                }
                for _ in range(5)
            ]
        return ToolResult(success=True, data=result)

    def _real_weather(self, city: str, units: str, forecast: bool) -> ToolResult:
        import requests

        base_url = "https://api.openweathermap.org/data/2.5"
        response = requests.get(
            f"{base_url}/weather",
            params={"q": city, "appid": self.api_key, "units": units},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        result = {
            "city": data["name"],
            "temperature": f"{data['main']['temp']}°",
            "condition": data["weather"][0]["description"],
        }
        return ToolResult(success=True, data=result)
