from powonline import model, schema


async def map_user(user: model.User) -> schema.UserSchema:
    avatar_url = await user.avatar_url
    return schema.UserSchema(
        name=user.name,
        active=user.active,
        email=user.email,
        avatar_url=avatar_url,
        confirmed_at=user.confirmed_at,
        inserted=user.inserted,
        updated=user.updated,
    )
