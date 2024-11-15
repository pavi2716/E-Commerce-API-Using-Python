from passlib.context import CryptContext
import bcrypt
import jwt
from dotenv import dotenv_values
from model import User
from fastapi import status,HTTPException

'''config_credential={
    "EMAIL": "pierce67@ethereal.email",
    "PW": "Jxd5R7ae18KkwsqeJy",
    "SECRET":'b53a6ab2f2e8c01725c0b5b0401a4bb458376fb0'
}'''

config_credential=dict(dotenv_values(".env"))

def hashed_password(password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')


async def verify_token(token:str):
    try:
        payload=jwt.decode(token,config_credential['SECRET'],algorithms=["HS256"])
        print("verify token payload",payload)
        user=await User.get(user_id=payload.get("id"))

    except:
        print("error")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token",
                            headers={"WWW-Authenticate":"Bearer"})
    return user

#login

async def token_generator(username:str,password:str):
    user=await authenticate_user(username,password)
    print("token_generator",user)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid username or password",
                            headers={"WWW.Authenticate":"Bearer"})
    token_data={"id":user.user_id,
                "username":user.username}
    token=jwt.encode(token_data,config_credential['SECRET'],algorithm="HS256")
    return token


async def authenticate_user(username,password):
    user=await User.get(username=username)
    print(user,"pavi")
    if user and await verify_password(password,user.password):
        return user
    return False


async def verify_password(plain_password,hashed_password):
   print("verify_password")
   return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))














