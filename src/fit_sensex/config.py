from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, field
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CREDENTIALS_FILE = PROJECT_ROOT / "credentials.ini"


def _read_credentials_file() -> configparser.SectionProxy | dict[str, str]:
    path = Path(os.getenv("KITE_CREDENTIALS_FILE", str(DEFAULT_CREDENTIALS_FILE)))
    if not path.exists():
        return {}

    parser = configparser.ConfigParser()
    parser.read(path)
    return parser["kite"] if parser.has_section("kite") else {}


_CREDENTIALS = _read_credentials_file()


@dataclass(frozen=True)
class ApiConfig:
    api_key: str = field(
        default_factory=lambda: os.getenv("KITE_API_KEY")
        or _CREDENTIALS.get("api_key", "")
    )
    access_token: str = field(
        default_factory=lambda: os.getenv("KITE_ACCESS_TOKEN")
        or _CREDENTIALS.get("access_token", "")
    )

    def validate(self) -> None:
        if not self.api_key or not self.access_token:
            raise ValueError(
                "Set KITE_API_KEY and KITE_ACCESS_TOKEN before starting the live app."
            )


@dataclass(frozen=True)
class StrikeConfig:
    low: int = int(os.getenv("LOW_STRIKE", "65000"))
    high: int = int(os.getenv("HIGH_STRIKE", "85000"))
    gap: int = int(os.getenv("STRIKE_GAP", "100"))


@dataclass(frozen=True)
class MarketConfig:
    user_value: int = int(os.getenv("USER_VALUE", "76300"))
    calendar_days: float = float(os.getenv("CALENDAR_DAYS", "255.5"))
    full_days: float = float(os.getenv("FULL_DAYS", "3"))
    intraday_var: float = float(os.getenv("INTRADAY_VAR", "0.4"))
    funding_rate: float = float(os.getenv("FUNDING_RATE", "0.055"))
    brokerage_rate: float = float(os.getenv("BROKERAGE_RATE", "0.0024"))
    risk_free_rate: float = float(os.getenv("RISK_FREE_RATE", "0.055"))
    atm_vol: float = float(os.getenv("ATM_VOL", "0.176"))
    refresh_ms: int = int(os.getenv("REFRESH_MS", "1000"))
    exchange: str = os.getenv("KITE_EXCHANGE", "BFO")
    symbol_name: str = os.getenv("SYMBOL_NAME", "SENSEX")
    holidays_file: Path = field(
        default_factory=lambda: Path(
            os.getenv("HOLIDAYS_FILE", str(PROJECT_ROOT / "hols.xlsx"))
        )
    )


@dataclass(frozen=True)
class ModelConfig:
    initial_a: float = float(os.getenv("INITIAL_A", "0.1527"))
    initial_bl: float = float(os.getenv("INITIAL_BL", "-0.063"))
    initial_br: float = float(os.getenv("INITIAL_BR", "-0.157"))
    initial_capl: float = float(os.getenv("INITIAL_CAPL", "0.485"))
    initial_floorr: float = float(os.getenv("INITIAL_FLOORR", "-0.50"))

    @property
    def initial_params(self) -> list[float]:
        return [
            self.initial_a,
            self.initial_bl,
            self.initial_br,
            self.initial_capl,
            self.initial_floorr,
        ]


@dataclass(frozen=True)
class AppConfig:
    api: ApiConfig = field(default_factory=ApiConfig)
    market: MarketConfig = field(default_factory=MarketConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    strikes: StrikeConfig = field(default_factory=StrikeConfig)
