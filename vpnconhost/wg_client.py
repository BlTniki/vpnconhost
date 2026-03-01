import subprocess
from typing import Optional, List
import logging

from config import Config


logger = logging.getLogger(__name__)


def _sudo_prefix() -> List[str]:
    """
    Config.SUDO_CMD: "sudo" / "sudo -n" / "".
    """
    logger.debug("Using sudo command: {}", Config.SUDO_CMD)
    cmd = (Config.SUDO_CMD or "").strip()
    return cmd.split() if cmd else []


def _run(args: list[str], *, input_text: Optional[str] = None) -> str:
    """
    Выполнить команду, вернуть stdout (str). При ошибке — RuntimeError.
    """
    logger.debug("Using sudo command: {}", Config.SUDO_CMD)
    args = _sudo_prefix() + args
    logger.debug("Executing wg command: {}", args)

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
        logger.debug("Failed to execute wg command: {}. Output: {}", args, out)
        raise RuntimeError(f"Command failed: {args}\nExit code: {e.returncode}\nOutput:\n{out}") from e


class _BaseWGClient:
    @staticmethod
    def create_private_key() -> str:
        return "private_lol_kek"

    @staticmethod
    def create_public_key(private_key: str) -> str:
        return "public_lol_kek"

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
    def add_peer_to_wg(peer_ip: str, public_key: str) -> str:
        return "Success"

    @staticmethod
    def remove_peer_from_wg(public_key: str) -> bool:
        return True


class _ImplementationWGClient(_BaseWGClient):
    @staticmethod
    def create_private_key() -> str:
        logger.debug("Creating private key")
        key = _run(["wg", "genkey"]).strip()
        return key

    @staticmethod
    def create_public_key(private_key: str) -> str:
        logger.debug("Creating public key")
        pub = _run(["wg", "pubkey"], input_text=private_key + "\n").strip()
        return pub

    @staticmethod
    def add_peer_to_wg(peer_ip: str, public_key: str) -> bool:
        ip = peer_ip if "/" in peer_ip else f"{peer_ip}/32"
        logger.info("Adding peer to wg with peer_ip={} and public_key={}", peer_ip, public_key)
        _run(["wg", "set", "wg0", "peer", public_key, "allowed-ips", ip])
        return True

    @staticmethod
    def remove_peer_from_wg(public_key: str) -> bool:
        logger.info("Removing peer from wg with public_key={}", public_key)
        _run(["wg", "set", "wg0", "peer", public_key, "remove"])
        return True


WGClient = _BaseWGClient if Config.WG_MOCK_MODE else _ImplementationWGClient
