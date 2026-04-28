import asyncio
from app.db.session import get_session_maker
from app.db.models.user import User
from app.db.services.auth_service import auth_service
from sqlalchemy import select

async def create_super_admin():
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Check if admin already exists
        result = await session.execute(select(User).where(User.email == "admin@kartr.com"))
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            admin_user = User(
                email="admin@gmail.com",
                password_hash=auth_service.hash_password("admin123"),
                full_name="Super Admin",
                user_type="admin",
                provider="email",
                email_verified="Y",
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            print("Admin user created successfully!")
        else:
            # Update password just in case
            admin_user.password_hash = auth_service.hash_password("admin123")
            admin_user.user_type = "admin"
            await session.commit()
            print("Admin user already existed, password reset to admin123")

if __name__ == "__main__":
    asyncio.run(create_super_admin())
