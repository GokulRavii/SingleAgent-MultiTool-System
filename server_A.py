from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import sys

# Create an MCP server
mcp = FastMCP(
    name="weather",
    host="0.0.0.0",  # only used for SSE transport (localhost)
    port=8000,  # only used for SSE transport (set this to any port)
)

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
    Event: {props.get('event', 'Unknown')}
    Area: {props.get('areaDesc', 'Unknown')}
    Severity: {props.get('severity', 'Unknown')}
    Description: {props.get('description', 'No description available')}
    Instructions: {props.get('instruction', 'No specific instructions provided')}
    """

@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
                {period['name']}:
                Temperature: {period['temperature']}°{period['temperatureUnit']}
                Wind: {period['windSpeed']} {period['windDirection']}
                Forecast: {period['detailedForecast']}
                """
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


from enum import Enum

class Operation(Enum):
    ADD = 'add'
    SUBSTRACT = "substract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"

@mcp.tool()
async def calc(a:float, b:float, operation:Operation) -> float:
    """Perform basic arithmetic operations between two numbers.
    
    Args:
        a: First number
        b: Second number
        operation: The operation to perform"""
    
    if operation == Operation.ADD:
        return a+b
    elif operation == Operation.SUBSTRACT:
        return a-b
    elif operation == Operation.MULTIPLY:
        return a*b
    elif operation == Operation.DIVIDE:
        if b == 0:
            raise ValueError("cannot divide by 0")
        else:
            return a/b
    else:
        raise ValueError("Unknown operation")


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
load_dotenv()

@mcp.tool()
async def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body text
    """

    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")
    host = os.getenv("EMAIL_HOST")
    port = int(os.getenv("EMAIL_PORT", 587))

    if not all([sender, password, host]):
        return "Email configuration is missing."

    try:
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)

        return f"Email successfully sent to {to}"

    except Exception as e:
        return f"Failed to send email: {str(e)}"

# Run the server
# if __name__ == "__main__":
#     transport = "sse"
#     if transport == "stdio":
#         print("Running server with stdio transport")
#         mcp.run(transport="stdio")
#     elif transport == "sse":
#         print("Running server with SSE transport")
#         mcp.run(transport="sse")
#     else:
#         raise ValueError(f"Unknown transport: {transport}")

if __name__ == "__main__":
    if "--stdio" in sys.argv:
        mcp.run(transport="stdio")
    else:
        print("Running server with SSE transport")
        mcp.run(transport="sse")

    
# uv run server/mcpserver/server.py

# uv run mcp dev server/mcpserver/server.py For mcp inspector