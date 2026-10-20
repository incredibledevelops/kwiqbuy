from typing import Optional

from beanie import PydanticObjectId

from app.core.security import hash_password, verify_password
from app.models.user import User, UserRole


async def get_by_email(email: str) -> Optional[User]:
    return await User.find_one(User.email == email.lower())


async def get_by_id(user_id: str) -> Optional[User]:
    try:
        return await User.get(PydanticObjectId(user_id))
    except Exception:
        return None


async def get_by_vendor_id(vendor_id: str) -> Optional[User]:
    try:
        vid = PydanticObjectId(vendor_id)
    except Exception:
        return None
    return await User.find_one(User.vendor_id == vid)


async def create_user(
    full_name: str,
    email: str,
    password: str,
    phone: Optional[str] = None,
    role: UserRole = UserRole.STAFF,
    vendor_id: Optional[str] = None,
    vehicle: Optional[str] = None,
    plate_number: Optional[str] = None,
) -> User:
    user = User(
        full_name=full_name,
        email=email.lower(),
        phone=phone,
        hashed_password=hash_password(password),
        role=role,
        vendor_id=PydanticObjectId(vendor_id) if vendor_id else None,
        vehicle=vehicle,
        plate_number=plate_number,
    )
    await user.insert()
    return user


async def list_users(
    role: Optional[UserRole] = None,
    vendor_id: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 500,
) -> list[User]:
    import re
    query = User.find()
    if role:
        query = query.find(User.role == role)
    if vendor_id:
        query = query.find(User.vendor_id == PydanticObjectId(vendor_id))
    if search:
        rx = re.escape(search.strip())
        query = query.find({
            "$or": [
                {"full_name": {"$regex": rx, "$options": "i"}},
                {"email": {"$regex": rx, "$options": "i"}},
                {"phone": {"$regex": rx, "$options": "i"}},
            ]
        })
    return await query.sort(+User.created_at).skip(skip).limit(limit).to_list()


async def update_user(user: User, data: dict) -> User:
    for k, v in data.items():
        if k == "vendor_id":
            user.vendor_id = PydanticObjectId(v) if v else None
        elif k == "password":
            user.hashed_password = hash_password(v)
        elif hasattr(user, k) and v is not None:
            setattr(user, k, v)
    await user.save()
    return user


async def delete_user(user: User) -> None:
    await user.delete()


async def change_password(
    user: User, current_password: str, new_password: str
) -> tuple[bool, str]:
    if not verify_password(current_password, user.hashed_password):
        return False, "Current password is incorrect"
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters"
    user.hashed_password = hash_password(new_password)
    await user.save()
    return True, ""


async def reset_password(user: User, new_password: str) -> None:
    user.hashed_password = hash_password(new_password)
    await user.save()


async def update_profile(
    user: User, full_name: Optional[str], phone: Optional[str]
) -> User:
    if full_name:
        user.full_name = full_name.strip()
    if phone is not None:
        user.phone = phone.strip() or None
    await user.save()
    return user