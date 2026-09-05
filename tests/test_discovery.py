from pathlib import Path

from src.discovery import discover_environment, parse_discovery


def test_parse_discovery_maps_machine_readable_values() -> None:
    environment = parse_discovery(
        "\n".join(
            [
                "OS_ID=ubuntu",
                "OS_VERSION=24.04",
                "KERNEL=Linux 6.8",
                "USER=demo",
                "IS_ROOT=false",
                "CONTAINER_TYPE=docker",
                "LYNIS=none",
                "SSH_CONFIG=/tmp/sshd_config",
                "PACKAGE_MANAGER=apt-get",
                "NETWORK_TOOL=ss",
            ]
        )
    )

    assert environment.os_id == "ubuntu"
    assert environment.is_container is True
    assert environment.is_root is False
    assert environment.ssh_config_path == "/tmp/sshd_config"
    assert environment.lynis_available is False


def test_missing_discovery_script_degrades_gracefully(tmp_path: Path) -> None:
    environment = discover_environment(tmp_path / "missing.sh")

    assert environment.os_id == "unknown"
    assert environment.limitations