"""Fail-closed target guards. Never include a DSN or driver exception in errors."""
from dataclasses import dataclass
from ipaddress import ip_address, ip_interface
from urllib.parse import unquote

from sqlalchemy.engine import make_url, URL

from app.core.config import DatabaseSettings, configuration


class TargetError(ValueError):
    pass


def canonical_server_address(value: str) -> str:
    """Compare exact host addresses; inet::text may include /32 or /128.

    Network prefixes never authorize another address in the same subnet.
    """
    try:
        if not isinstance(value, str) or '%' in value:
            raise ValueError()
        address = ip_interface(value)
        if address.network.prefixlen != address.max_prefixlen:
            raise ValueError()
        return address.ip.compressed
    except ValueError:
        raise TargetError('Authenticated server address rejected.') from None


def instance_matches(address, port, expected_address, expected_port) -> bool:
    try:
        return (type(port) is int and type(expected_port) is int and port == expected_port
                and canonical_server_address(address) == canonical_server_address(expected_address))
    except TargetError:
        return False


@dataclass(frozen=True)
class Target:
    host: str
    port: int
    database: str
    role: str


def parse_target(raw: str, *, maintenance: bool, testing: bool) -> tuple[URL, Target]:
    try:
        u = make_url(raw)
        host = (u.host or '').lower()
        # Resolve approved loopback aliases ourselves; never leave libpq routing options.
        host = '127.0.0.1' if host == 'localhost' else host
        if not ip_address(host).is_loopback:
            raise ValueError()
        host = ip_address(host).compressed
        role = 'finance_tax_migrator' if maintenance else 'finance_tax_app'
        db = 'finance_tax_test' if testing else 'finance_tax_dev'
        if (u.drivername != 'postgresql+psycopg' or u.query or u.username != role
                or u.database != db or unquote(u.database) != db
                or ',' in host or (u.port or 5432) != 5432):
            raise ValueError()
        return u.set(host=host, port=u.port or 5432), Target(host, u.port or 5432, db, role)
    except Exception:
        raise TargetError('Database target rejected; check explicit project target and role.') from None


def test_settings(values: dict[str, str] | None = None) -> tuple[DatabaseSettings, DatabaseSettings]:
    v = configuration() if values is None else values
    if v.get('app_env') != 'test' or v.get('pytest_xdist_worker'):
        raise TargetError('Serial APP_ENV=test is required.')
    pair = []
    targets = []
    for key, maintenance in [('test_database_url', False), ('test_migration_database_url', True)]:
        raw = v.get(key, '')
        u, t = parse_target(raw, maintenance=maintenance, testing=True)
        pair.append(DatabaseSettings(database_url=u.render_as_string(hide_password=False)))
        targets.append(t)
    if targets[0].host != targets[1].host or targets[0].port != targets[1].port:
        raise TargetError('Test connections must identify the same instance.')
    for key in ('database_url', 'migration_database_url'):
        if v.get(key):
            try:
                u = make_url(v[key])
                host = '127.0.0.1' if (u.host or '').lower() == 'localhost' else u.host
                if u.query or (host, u.port or 5432, unquote(u.database or '')) == (targets[0].host, targets[0].port, targets[0].database):
                    raise ValueError()
            except Exception:
                raise TargetError('Test target is ambiguous or equals an application target.') from None
    return tuple(pair)


def verify_authenticated(cursor, target: Target):
    cursor.execute("""SELECT current_database(), session_user, current_user,
        current_setting('server_version_num')::int, inet_server_addr()::text,
        inet_server_port(), r.rolsuper, r.rolcreatedb, r.rolcreaterole,
        r.rolreplication, r.rolbypassrls,
        EXISTS (SELECT 1 FROM pg_catalog.pg_auth_members m WHERE m.member=r.oid),
        pg_catalog.pg_get_userbyid(d.datdba), pg_catalog.pg_encoding_to_char(d.encoding),
        (SELECT pg_catalog.pg_get_userbyid(nspowner) FROM pg_catalog.pg_namespace WHERE nspname='harness')
        FROM pg_catalog.pg_roles r CROSS JOIN pg_catalog.pg_database d
        WHERE r.rolname=current_user AND d.datname=current_database()""")
    r = cursor.fetchone()
    if (not r or r[:3] != (target.database, target.role, target.role)
            or not 180000 <= r[3] < 190000 or not instance_matches(r[4], r[5], target.host, target.port)
            or any(r[6:12]) or r[12:] != ('finance_tax_migrator', 'UTF8','finance_tax_migrator')):
        raise TargetError('Authenticated database identity, instance or ownership rejected.')
