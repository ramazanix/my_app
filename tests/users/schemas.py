user_base = {"name": str}
user = {
    "id": str,
    "username": str,
    "created_at": str,
    "updated_at": str,
    "role": {"name": str, "description": str},
    "avatar": {"name": str, "size": int, "location": str},
}

users_base: list[user_base] = [user_base]
users: list[user] = [user]
