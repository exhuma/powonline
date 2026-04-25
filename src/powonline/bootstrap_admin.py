import argparse
import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from powonline.core import User as UserCore
from powonline.model import Role, User, get_dsn


async def bootstrap(username, password):
    dsn = get_dsn()
    if not dsn:
        print("Error: POWONLINE_DSN environment variable not set.")
        return

    engine = create_async_engine(dsn)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # 1. Ensure 'admin' role exists
        admin_role = await Role.get_or_create(session, "admin")

        # 2. Find or create user
        user = await UserCore.get(session, username)
        if not user:
            print(f"Creating user {username}...")
            user = User(name=username, password=password)
            session.add(user)
        else:
            print(f"Updating password for user {username}...")
            user.setpw(password)

        # 3. Assign admin role
        user_roles = await user.awaitable_attrs.roles
        if admin_role not in user_roles:
            print(f"Assigning 'admin' role to {username}...")
            user_roles.add(admin_role)

        await session.commit()

    await engine.dispose()
    print(f"Successfully bootstrapped {username} as an admin.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap an admin user.")
    parser.add_argument("username", help="Admin username")
    parser.add_argument("password", help="Admin password")
    args = parser.parse_args()

    asyncio.run(bootstrap(args.username, args.password))
