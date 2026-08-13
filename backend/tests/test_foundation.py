from app.core.config import Settings
from app.database.base import Base
from app.models import Company, Device


def test_settings_have_safe_local_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url.startswith("postgresql+psycopg://")
    assert settings.ssh_identity_container_prefix == "/run/ssh-keys"


def test_foundation_models_are_registered() -> None:
    assert Company.__table__.name == "companies"
    assert Device.__table__.name == "devices"
    assert {"companies", "devices"}.issubset(Base.metadata.tables)
