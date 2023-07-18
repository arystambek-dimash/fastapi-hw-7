from fastapi import FastAPI, Depends, Form, Cookie
from fastapi.responses import Response
from fastapi.requests import Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
import json

from fastapi.exceptions import HTTPException
from .flowers_repository import Flower, FlowersRepository
from .purchases_repository import Purchase, PurchasesRepository
from .users_repository import User, UsersRepository

app = FastAPI()

flowers_repository = FlowersRepository()
purchases_repository = PurchasesRepository()
users_repository = UsersRepository()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(user_id):
    body = {"user_id": user_id}
    token = jwt.encode(body, "flower", algorithm="HS256")
    return token


def decode_access_token(token):
    data = jwt.decode(token, "flower", algorithms=["HS256"])
    return data["user_id"]


def get_current_active_user(token: str = Depends(oauth2_scheme)):
    user_id = decode_access_token(token)
    user = users_repository.get_one_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user token")
    return user


@app.post("/signup")
def signup(username: str = Form(...), email: str = Form(...), full_name: str = Form(...), password: str = Form(...)):
    user = User(username=username, email=email, full_name=full_name, password=password)
    user.id = users_repository.get_next_id()
    users_repository.save(user)
    return user


@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = users_repository.get_user_by_username(username)
    if not user or user.password != password:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token(user.id)
    return {"access_token": token, "type": "bearer"}


@app.get("/profile")
def profile(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/flowers")
def flowers_get():
    return flowers_repository.get_all()


@app.post("/flowers")
def flowers_post(name: str = Form(...), count: int = Form(...), cost: float = Form()):
    flower = Flower(name=name, cost=cost, count=count)
    flowers_repository.save(flower)
    return {"flower_id": flower.id}


@app.get("/cart/items")
def cart_items_get(request: Request, token: str = Depends(oauth2_scheme)):
    user_cart = request.cookies.get(token)
    if not user_cart:
        return {"message":"The cart is empty"}
    flowers = []
    new_user_cart = user_cart.replace('[', '').replace(']', '')
    new_user_cart = new_user_cart.split(",")
    total_cost = 0
    for i in new_user_cart:
        flower_id = int(i)
        flower = flowers_repository.get_by_id(flower_id)
        flowers.append(flower)
        total_cost += flower.cost

    return {"flowers_in_cart": flowers, "total_cost": total_cost}


@app.post("/cart/items")
def cart_items_post(flower_id: int = Form(...), token: str = Depends(oauth2_scheme), cart: str = Cookie(default="[]")):
    cart_json = json.loads(cart)
    response = Response('{"msg":"The flower has been successfully added to the basket"}', status_code=200)
    if flower_id:
        flowers_repository.save_flower_to_cart(flower_id)
        cart_json.append(flowers_repository.get_all_in_cart())
        new_cart = json.dumps(cart_json)
        response.set_cookie(key=token, value=new_cart)
        return response
    return {"msg": "The flower cannot be found"}


@app.post("/purchases")
def purchases(request: Request, flower_id: str = Form(), token: str = Depends(oauth2_scheme)):
    user_cart = request.cookies.get(token)
    if not json.loads(user_cart):
        return {"message":"The cart is empty"}
    flowers = []
    new_user_cart = user_cart.replace('[', '').replace(']', '')
    new_user_cart = new_user_cart.split(",")
    for i in new_user_cart:
        flower_id = int(i)
        flowers.append(flower_id)
    flowers = sorted(flowers)

    if flower_id:
        purchases_repository.save(Purchase(user_id=decode_access_token(token), flower_id=flower_id))

        for i,f in enumerate(flowers):
            if f == flower_id:
                del flowers[i]
                break
        response = Response("The flower was successfully paid", status_code=200)
        new_cart = json.dumps(flowers)
        response.set_cookie(key=token, value=new_cart)
        return response

    raise HTTPException(status_code=400, detail=f"Not a valid flower ID: {flower_id}")


@app.get("/purchases")
def purchases():
    flowers_purchases = []
    for p in purchases_repository.get_all():
        flower = flowers_repository.get_by_id(p)
        flowers_purchases.append({"Name: " : flower.name,"Cost: ": flower.cost})

    return flowers_purchases
