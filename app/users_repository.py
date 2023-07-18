from pydantic import BaseModel, Field, EmailStr
from fastapi.exceptions import HTTPException


class User(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8)
    id: int = 0


class UsersRepository:
    users: list[User]

    def __init__(self):
        self.users = [User(username="d",email="test@test.com",full_name="D",password="12345678",id=1)]

    def save(self, user):
        for u in self.users:
            if user.email == u.email or user.username == u.username:
                raise HTTPException(status_code=400, detail="The email or username already exists")

        user.id = self.get_next_id()
        self.users.append(user)

    def get_one_by_id(self, user_id) -> User:
        for i, u in enumerate(self.users):
            if u.id == user_id:
                return self.users[i]
        return None

    def get_user_by_username(self, username) -> User:
        for i, u in enumerate(self.users):
            if u.username == username:
                return self.users[i]
        return None

    def get_next_id(self):
        return len(self.users) + 1
