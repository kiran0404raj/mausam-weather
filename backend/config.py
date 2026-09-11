import os

class Settings:
    PROJECT_NAME: str = "Py SIH Weather Intelligence"
    VERSION: str = "1.0.0"
    DEFAULT_LAT: float = 12.9716  # Bengaluru
    DEFAULT_LON: float = 77.5946
    DEFAULT_CITY: str = "Bengaluru"
    DEFAULT_COUNTRY: str = "India"
    API_TIMEOUT: float = 12.0

settings = Settings()
