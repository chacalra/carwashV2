"""CLI entrypoint.

Uso:
  uv run python -m backend.cli set-branding --subdomain demo --logo https://... --primary "#FF0000"
  uv run python -m backend.cli clear-branding --subdomain demo
  uv run python -m backend.cli show-tenant --subdomain demo
  uv run python -m backend.cli create-tenant --subdomain demo --name "Demo SA" \
      --responsible "Ana Perez" --admin-username admin --admin-password "..."
"""

import argparse
import json
import sys

from backend.cli import branding as branding_cmd
from backend.cli import create_tenant as create_tenant_cmd
from backend.database.connection import SessionLocal


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="backend.cli",
        description="Operaciones administrativas sobre tenants.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # set-branding
    p_set = sub.add_parser(
        "set-branding",
        help="Setea branding del tenant (solo los campos pasados).",
    )
    p_set.add_argument("--subdomain", required=True)
    p_set.add_argument("--logo", help="URL del logo (light).")
    p_set.add_argument("--logo-dark", help="URL del logo para dark mode.")
    p_set.add_argument("--primary", help="Color primario hex (#RGB / #RRGGBB / #RRGGBBAA).")
    p_set.add_argument("--secondary", help="Color secundario hex.")
    show = p_set.add_mutually_exclusive_group()
    show.add_argument(
        "--show-mukusoft",
        dest="show_mukusoft",
        action="store_true",
        default=None,
        help="Muestra el 'powered by Mukusoft'.",
    )
    show.add_argument(
        "--hide-mukusoft",
        dest="show_mukusoft",
        action="store_false",
        help="Oculta el 'powered by Mukusoft'.",
    )

    # clear-branding
    p_clear = sub.add_parser(
        "clear-branding",
        help="Borra logos y colores del tenant. No toca mostrar_marca_mukusoft.",
    )
    p_clear.add_argument("--subdomain", required=True)

    # show-tenant
    p_show = sub.add_parser(
        "show-tenant",
        help="Imprime el branding actual del tenant.",
    )
    p_show.add_argument("--subdomain", required=True)

    # create-tenant
    p_create = sub.add_parser(
        "create-tenant",
        help="Alta atómica: lavandería + rol admin + permisos + usuario admin.",
    )
    p_create.add_argument("--subdomain", required=True)
    p_create.add_argument("--name", required=True, help="Nombre del local.")
    p_create.add_argument("--responsible", required=True, help="Nombre del responsable.")
    p_create.add_argument("--admin-username", required=True)
    p_create.add_argument("--admin-password", required=True)
    p_create.add_argument("--email")
    p_create.add_argument("--phone")

    return parser


def main(argv=None):
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "create-tenant":
            # create-tenant maneja su propia sesión porque es una transacción
            # multi-paso con rollback en error.
            result = create_tenant_cmd.create_tenant(
                subdomain=args.subdomain,
                name=args.name,
                responsible=args.responsible,
                admin_username=args.admin_username,
                admin_password=args.admin_password,
                email=args.email,
                phone=args.phone,
            )
        else:
            with SessionLocal() as session:
                if args.command == "set-branding":
                    result = branding_cmd.set_branding(
                        session,
                        subdomain=args.subdomain,
                        logo=args.logo,
                        logo_dark=args.logo_dark,
                        primary=args.primary,
                        secondary=args.secondary,
                        show_mukusoft=args.show_mukusoft,
                    )
                elif args.command == "clear-branding":
                    result = branding_cmd.clear_branding(session, subdomain=args.subdomain)
                elif args.command == "show-tenant":
                    result = branding_cmd.show_branding(session, subdomain=args.subdomain)
                else:
                    parser.error(f"Comando desconocido: {args.command}")
                    return 2
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
