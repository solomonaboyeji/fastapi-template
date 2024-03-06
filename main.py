from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List, Union
import psycopg2
from psycopg2 import sql
from fastapi import Security
import smtplib
from email.mime.multipart import MIMEMultipart
from fastapi.middleware.cors import CORSMiddleware
from email.mime.text import MIMEText
import secrets
import string

from fastapi_utils.openapi import simplify_operation_ids

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Sample connection to a PostgreSQL database
DB_CONN_STRING = "dbname='your_dbname' user='your_username' host='your_host' password='your_password'"

# Email configurations
EMAIL_HOST = "smtp.example.com"
EMAIL_PORT = 587
EMAIL_ADDRESS = "your-email@example.com"
EMAIL_PASSWORD = "your-email-password"
EMAIL_FROM_NAME = "Your App Name"

app = FastAPI()

simplify_operation_ids(app)

# Custom OpenAPI schema extension function
def add_scopes_to_description(route):
    # print(route)
    import pprint
    pprint.pprint(route)
    required_scopes = route.dependencies[0].scopes
    route.summary = f"{route.summary} (Required Scopes: {', '.join(required_scopes)})"
    return route

# @app.on_event("startup")
# async def add_scopes_to_docs():
#     for route in app.routes:

#         route.operation_id = route.name
#         import pprint
#         pprint.pprint(route.__dict__)
#         print("\n")
#         if "dependencies" in route.__dict__ and route.__dict__.get("dependencies"):
#             route_path = route.path
#             app.openapi_schema["paths"][route_path] = add_scopes_to_description(route.__dict__)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    scopes: Optional[List[str]] = []
    email_verified: Optional[bool] = False

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str = None
    scopes: List[str] = []

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenPayload(BaseModel):
    sub: str = None
    exp: datetime = None
    scopes: List[str] = []

class Item(BaseModel):
    name: str

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    password: str

class EmailConfirmationException(Exception):
    pass

class PasswordResetException(Exception):
    pass

class PasswordResetToken(BaseModel):
    email: str
    token: str

def get_db():
    db = getattr(get_db, "_db", None)
    if db is None:
        db = psycopg2.connect(DB_CONN_STRING)
        setattr(get_db, "_db", db)
    return db

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        scopes: List[str] = payload.get("scopes", [])
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, scopes=scopes)
    except JWTError:
        raise credentials_exception
    return token_data

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def has_required_scopes(required_scopes: List[str] = Depends()):
    def _has_required_scopes(current_user: User = Depends(get_current_user)):
        for scope in required_scopes:
            if scope not in current_user.scopes:
                raise HTTPException(status_code=403, detail="Not enough permissions")
        return current_user
    return _has_required_scopes

def send_email(subject: str, to_email: str, body: str):
    msg = MIMEMultipart()
    msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_ADDRESS}>"
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()
    except Exception as e:
        raise EmailConfirmationException("Failed to send email for email confirmation")

class ItemService:
    @staticmethod
    def create_item(item: Item, current_user: User) -> Union[Item, Exception]:
        # You can access current_user here to check scopes
        return Item(name=item.name)

    @staticmethod
    def delete_item(item_id: int, current_user: User) -> Union[dict, Exception]:
        # You can access current_user here to check scopes
        return {"message": f"Item {item_id} deleted"}

    @staticmethod
    def update_item(item_id: int, item: Item, current_user: User) -> Union[Item, Exception]:
        # You can access current_user here to check scopes
        return Item(name=item.name)

class UserService:
    @staticmethod
    def get_user(email: str) -> Union[User, Exception]:
        db = get_db()
        cur = db.cursor()
        cur.execute(sql.SQL("SELECT * FROM users WHERE email = %s"), (email,))
        row = cur.fetchone()
        if row:
            user_dict = {
                "username": row[0],
                "email": row[1],
                "full_name": row[2],
                "disabled": row[3],
                "hashed_password": row[4],
                "scopes": row[5] if row[5] else [],  # Fetch scopes or set to empty list if None
                "email_verified": row[6]
            }
            return User(**user_dict)
        return Exception("User not found")

    @staticmethod
    def create_user(user: UserCreate) -> Union[User, Exception]:
        db = get_db()
        hashed_password = get_password_hash(user.password)
        cur = db.cursor()
        try:
            cur.execute(sql.SQL("INSERT INTO users (username, email, full_name, disabled, hashed_password, email_verified) VALUES (%s, %s, %s, %s, %s, %s)"), (user.username, user.email, user.full_name, False, hashed_password, False))
            db.commit()
        except psycopg2.IntegrityError as e:
            db.rollback()
            if 'duplicate' in str(e).lower():
                return HTTPException(status_code=409, detail="User with this email already exists")
            else:
                return HTTPException(status_code=500, detail="Error while creating user")
        # Send email for email confirmation
        confirmation_token = secrets.token_hex(16)
        confirmation_link = f"http://yourapp.com/confirm_email?token={confirmation_token}"
        email_body = f"Please confirm your email by clicking on the link below:\n{confirmation_link}"
        send_email("Confirm Your Email", user.email, email_body)
        return User(username=user.username, email=user.email, full_name=user.full_name)

    @staticmethod
    def confirm_email(token: str) -> Union[User, Exception]:
        db = get_db()
        cur = db.cursor()
        cur.execute(sql.SQL("UPDATE users SET email_verified = TRUE WHERE confirmation_token = %s"), (token,))
        if cur.rowcount == 0:
            return Exception("Invalid confirmation token")
        db.commit()
        return User(email_verified=True)

    @staticmethod
    def request_password_reset(email: str) -> Union[PasswordResetToken, Exception]:
        db = get_db()
        cur = db.cursor()
        # Generate and save reset token
        reset_token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        cur.execute(sql.SQL("UPDATE users SET reset_token = %s, reset_token_expiry = NOW() + INTERVAL '10 minutes' WHERE email = %s"), (reset_token, email))
        if cur.rowcount == 0:
            return Exception("User not found")
        db.commit()
        # Send email with reset token
        reset_link = f"http://yourapp.com/reset_password?token={reset_token}"
        email_body = f"Please use the following link to reset your password:\n{reset_link}"
        send_email("Reset Your Password", email, email_body)
        return PasswordResetToken(email=email, token=reset_token)

    @staticmethod
    def reset_password(token: str, new_password: str) -> Union[User, Exception]:
        db = get_db()
        cur = db.cursor()
        # Check if token is valid
        cur.execute(sql.SQL("SELECT email FROM users WHERE reset_token = %s AND reset_token_expiry >= NOW()"), (token,))
        row = cur.fetchone()
        if not row:
            return Exception("Invalid or expired token")
        email = row[0]
        # Update password
        hashed_password = get_password_hash(new_password)
        cur.execute(sql.SQL("UPDATE users SET hashed_password = %s, reset_token = NULL, reset_token_expiry = NULL WHERE email = %s"), (hashed_password, email))
        db.commit()
        return User(email=email)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": user.scopes}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

def authenticate_user(username: str, password: str) -> Union[User, None]:
    user = UserService.get_user(username)
    if isinstance(user, User):
        if not verify_password(password, user.hashed_password):
            return None
        return user
    return None

@app.post("/users/", response_model=User)
async def create_user(user: UserCreate):
    user_or_exception = UserService.create_user(user)
    if isinstance(user_or_exception, User):
        return user_or_exception
    else:
        raise user_or_exception

@app.get("/confirm_email/")
async def confirm_email(token: str):
    result = UserService.confirm_email(token)
    if isinstance(result, User):
        return {"message": "Email confirmed successfully"}
    else:
        raise HTTPException(status_code=400, detail=str(result))

@app.post("/request_password_reset/")
async def request_password_reset(email: str):
    result = UserService.request_password_reset(email)
    if isinstance(result, PasswordResetToken):
        return {"message": "Password reset email sent successfully"}
    else:
        raise HTTPException(status_code=400, detail=str(result))

@app.post("/reset_password/")
async def reset_password(token: str, new_password: str):
    result = UserService.reset_password(token, new_password)
    if isinstance(result, User):
        return {"message": "Password reset successful"}
    else:
        raise HTTPException(status_code=400, detail=str(result))

# items

@app.post("/items/", response_model=Item)
async def create_item(item: Item, current_user: User = Security(has_required_scopes(["create_item"])) ):
    ItemService.create_item(item, current_user)
    return item

@app.delete("/items/{item_id}", status_code=200)
async def delete_item(item_id: int, current_user: User = Depends(has_required_scopes(["delete_item"]))):
    ItemService.delete_item(item_id, current_user)
    return {"message": f"Item {item_id} deleted"}

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item, current_user: User = Security(has_required_scopes(["update_item"]), scopes=["update_item", "create_item"])):
    ItemService.update_item(item_id, item, current_user)
    return item


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    max_age=600,
    allow_headers=["*"],
    # allow_origin_regex="",
)



import pprint

if not app.openapi_schema:

    from fastapi.openapi.utils import get_openapi
    openapi_schema = get_openapi(title="FastAPI", version="0.1", routes=app.routes)
    app.openapi_schema = openapi_schema

# pprint.pprint(app.openapi_schema)
for route in app.routes:

    route.operation_id = route.name
    WHAT IS GOING ON!
    # pprint.pprint(type(app.openapi_schema["paths"]))
    # for pth in app.openapi_schema["paths"]:
    #     for method in app.openapi_schema["paths"][pth]:
    #         method_data = app.openapi_schema["paths"][pth][method]
    #         if "security" in method_data:
    #             for oa2pb in method_data["security"]:
    #                 for scope in oa2pb["OAuth2PasswordBearer"]:
    #                     print(route, pth, method, scope)

            # print("security" in app.openapi_schema["paths"][pth][method])
    if "dependencies" in route.__dict__ and route.__dict__.get("dependencies"):
        route_path = route.path
        app.openapi_schema["paths"][route_path] = add_scopes_to_description(route.__dict__)