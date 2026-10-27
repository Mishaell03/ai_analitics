import logging
from ipaddress import ip_address
from typing import Optional
from starlette.requests import HTTPConnection
from app.core.config import settings

logger = logging.getLogger(__name__)


def safe_inet_ip(value: str | None, default: str | None = None) -> str | None:
    """Валидирует строку IP для безопасной вставки в колонку PostgreSQL INET.

    Если значение не является валидным IPv4/IPv6 адресом, возвращает default.
    """
    if value:
        try:
            return str(ip_address(value.strip()))
        except ValueError:
            pass
    return default


def is_trusted_proxy(ip: str | None) -> bool:
    """Проверяет, входит ли указанный IP в доверенные сети прокси."""
    if not ip:
        return False

    try:
        parsed_ip = ip_address(ip.strip())
        return any(
            parsed_ip in network
            for network in settings.trusted_proxies
        )
    except ValueError:
        return False


def get_client_ip(request: HTTPConnection) -> Optional[str]:
    """Определяет реальный IP клиента с учётом доверенных обратных прокси.

    Заголовки пересылки (X-Forwarded-For, X-Real-IP) учитываются ТОЛЬКО если
    непосредственное соединение установлено от доверенного прокси (peer).
    В X-Forwarded-For поиск ведётся справа налево, чтобы злоумышленник не мог
    обойти проверку или подделать IP, добавив свой заголовок с левого края.
    """
    if request.client is None or not request.client.host:
        return None

    peer_ip = request.client.host.strip()

    # Если непосредственный отправитель не является доверенным прокси,
    # любые заголовки пересылки игнорируются
    if not is_trusted_proxy(peer_ip):
        return safe_inet_ip(peer_ip)

    # Непосредственный отправитель — доверенный прокси.
    # Анализируем цепочку X-Forwarded-For справа налево.
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        raw_ips = [item.strip() for item in forwarded_for.split(",") if item.strip()]
        for candidate_raw in reversed(raw_ips):
            candidate_ip = safe_inet_ip(candidate_raw)
            if candidate_ip is None:
                # Пропускаем некорректные IP-значения
                continue
            if not is_trusted_proxy(candidate_ip):
                return candidate_ip

        # Если все IP в заголовке доверенные, возвращаем самый левый валидный
        for candidate_raw in raw_ips:
            candidate_ip = safe_inet_ip(candidate_raw)
            if candidate_ip:
                return candidate_ip

    # Если X-Forwarded-For отсутствует, проверяем X-Real-IP от доверенного прокси
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        candidate_ip = safe_inet_ip(real_ip)
        if candidate_ip:
            return candidate_ip

    return safe_inet_ip(peer_ip)


# GEO IP
def get_geoip(ip: str) -> tuple[Optional[str], Optional[bool]]:
    """Определяет страну и признак прокси по IP через базу MaxMind."""
    if not settings.geoip_db_path:
        return None, None

    try:
        import geoip2.database
        from geoip2.errors import AddressNotFoundError

        with geoip2.database.Reader(settings.geoip_db_path) as reader:
            response = reader.country(ip)

            country_code = (
                response.country.iso_code
                if response.country
                else None
            )

            traits = response.traits

            is_proxy = any([
                getattr(traits, "is_public_proxy", False),
                getattr(traits, "is_satellite_provider", False),
                getattr(traits, "is_tor_exit_node", False),
                getattr(traits, "is_hosting_provider", False),
            ])

            return country_code, is_proxy

    except AddressNotFoundError:
        return None, None

    except Exception as e:
        logger.debug(f"geoip resolution failed: {e}")
        return None, None
