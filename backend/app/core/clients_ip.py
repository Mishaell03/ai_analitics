from ipaddress import ip_address
from starlette.requests import HTTPConnection
from app.core.config import settings
import geoip2.database
from geoip2.errors import AddressNotFoundError
from typing import Optional

# GET CLIENT IP
def is_trusted_proxy(ip: str) -> bool:
    parsed_ip = ip_address(ip)

    return any(
        parsed_ip in network
        for network in settings.trusted_proxies
    )


def get_client_ip(request: HTTPConnection) -> Optional[str]:
    if request.client is None:
        return None

    proxy_ip = request.client.host

    if is_trusted_proxy(proxy_ip):
        forwarded_for = request.headers.get("x-forwarded-for")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")

        if real_ip:
            return real_ip.strip()

    return proxy_ip

# GEO IP
def get_geoip(ip: str) -> tuple[Optional[str], Optional[bool]]:

    try:
        with geoip2.database.Reader(settings.geoip_db_path) as reader:
            response = reader.country(ip)

            country_code = (
               response.country.iso_code
                if response.country
                else None
            )

            traits = response.traits

            is_proxy = any([
                traits.is_public_proxy,
                traits.is_satellite_provider,
                traits.is_tor_exit_node,
                traits.is_public_proxy,
                traits.is_hosting_provider,
            ])

            return country_code, is_proxy
    except AddressNotFoundError:
        return None, None

    except Exception as e:
        print(e)
        return None, None