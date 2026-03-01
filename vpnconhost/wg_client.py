import subprocess
from typing import Optional, List
import logging

from config import Config


logger = logging.getLogger(__name__)


def _sudo_prefix() -> List[str]:
    """
    Config.SUDO_CMD: "/usr/bin/sudo" / "/usr/bin/sudo -n" / "".
    """
    cmd = (Config.SUDO_CMD or "").strip()
    return cmd.split() if cmd else []


def _run(args: list[str], *, input_text: Optional[str] = None, use_sudo: bool = False) -> str:
    """
    Выполнить команду, вернуть stdout (str). При ошибке — RuntimeError.

    Args:
        args: Команда и аргументы
        input_text: Входные данные для stdin
        use_sudo: Использовать ли sudo (только для команд, требующих привилегий)
    """
    if use_sudo:
        args = _sudo_prefix() + args
    logger.debug("Executing wg command: %s", args)
    if Config.WG_MOCK_MODE:
        return "mock_output"
    try:
        p = subprocess.run(
            args,
            input=(input_text.encode("utf-8") if input_text is not None else None),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )
        return p.stdout.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        out = (e.stdout or b"").decode("utf-8", errors="replace")
        logger.debug("Failed to execute wg command: %s. Output: %s", args, out)
        raise RuntimeError(f"Command failed: {args}\nExit code: {e.returncode}\nOutput:\n{out}") from e
    except FileNotFoundError as e:
        logger.error("Command not found: %s. Error: %s", args, e)
        raise RuntimeError(f"Command not found: {args[0]}. Make sure it's installed and in PATH.") from e


class WGClient:
    @staticmethod
    def create_private_key() -> str:
        logger.debug("Creating private key")
        key = _run([Config.WG_CMD, "genkey"]).strip()
        return key

    @staticmethod
    def create_public_key(private_key: str) -> str:
        logger.debug("Creating public key")
        pub = _run([Config.WG_CMD, "pubkey"], input_text=private_key + "\n").strip()
        return pub

    @staticmethod
    def get_peer_conf(peer_ip: str, private_key: str) -> str:
        endpoint = Config.SERVER_ADDRESS

        text = (
            "[Interface]\n"
            f"PrivateKey = {private_key}\n"
            f"Address = {peer_ip}\n"
            f"DNS = {Config.WG_DNS}\n"
            "[Peer]\n"
            f"PublicKey = {Config.WG_PUBLIC_KEY}\n"
            "AllowedIPs = 0.0.0.0/0, ::/0\n"
            f"Endpoint = {endpoint}\n"
        )
        return text

    @staticmethod
    def add_peer_to_wg(peer_ip: str, public_key: str) -> bool:
        ip = peer_ip if "/" in peer_ip else f"{peer_ip}/32"
        logger.info("Adding peer to wg with peer_ip=%s and public_key=%s", peer_ip, public_key)
        _run([Config.WG_CMD, "set", "wg0", "peer", public_key, "allowed-ips", ip], use_sudo=True)
        return True

    @staticmethod
    def remove_peer_from_wg(public_key: str) -> bool:
        logger.info("Removing peer from wg with public_key=%s", public_key)
        _run([Config.WG_CMD, "set", "wg0", "peer", public_key, "remove"], use_sudo=True)
        return True
