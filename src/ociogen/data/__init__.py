from pathlib import Path
import os

def _get_package_config_path() -> Path:
    """
    Returns the path to the package config settings file.
    """
    return Path(__file__).parent / "config.yaml"


def _get_local_config_path() -> Path:
    """
    Returns the path to the local config settings file.
    """
    _package_name = "ociogen"
    _local_config_path = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    return _local_config_path/f"{_package_name}/config.yaml"

def _copy_package_config_to_local():
    """
    Copies the package config settings file to the local config directory.
    """
    package_config_path = _get_package_config_path()
    local_config_path = _get_local_config_path()
    
    if not local_config_path.exists():
        os.makedirs(local_config_path.parent, exist_ok=True)
        with open(package_config_path, "r") as package_file:
            with open(local_config_path, "w") as local_file:
                local_file.write(package_file.read())

PACKAGE_CONFIG_PATH = _get_package_config_path()
LOCAL_CONFIG_PATH = _get_local_config_path()

__all__ = [
    "PACKAGE_CONFIG_PATH",
    "LOCAL_CONFIG_PATH",
]
