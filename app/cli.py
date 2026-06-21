import argparse

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.bootstrap import seed_admin_user


def seed_admin(args: argparse.Namespace) -> int:
    settings = get_settings()
    if settings.app_env.lower() == "production":
        print("Refusing to seed an admin while APP_ENV=production.")
        return 1

    db = SessionLocal()
    try:
        user, created = seed_admin_user(
            db,
            email=args.email,
            password=args.password,
            full_name=args.full_name,
        )
    finally:
        db.close()

    action = "created" if created else "updated"
    print(f"Admin user {action}: {user.email}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Expense Approval System CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_admin_parser = subparsers.add_parser(
        "seed-admin",
        help="Create or update a development/demo admin user.",
    )
    seed_admin_parser.add_argument("--email", required=True)
    seed_admin_parser.add_argument("--password", required=True)
    seed_admin_parser.add_argument("--full-name", required=True)
    seed_admin_parser.set_defaults(func=seed_admin)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
