from fastapi import BackgroundTasks,UploadFile,File,Form,Depends,HTTPException,status
from fastapi_mail import FastMail,MessageSchema,ConnectionConfig,MessageType
from dotenv import dotenv_values
from  pydantic import BaseModel,EmailStr
from typing import List
from model import User
import jwt


config_credential={
    "EMAIL": "pierce67@ethereal.email",
    "PW": "Jxd5R7ae18KkwsqeJy",
    "SECRET":'b53a6ab2f2e8c01725c0b5b0401a4bb458376fb0'
}


conf=ConnectionConfig(MAIL_USERNAME=config_credential["EMAIL"],
                      MAIL_PASSWORD=config_credential["PW"],
                      MAIL_FROM=config_credential["EMAIL"],
                      MAIL_PORT=587,
                      MAIL_SERVER="smtp.ethereal.email",
                      USE_CREDENTIALS=True,
                      MAIL_STARTTLS=True, # Ensure this is included
                      MAIL_SSL_TLS=False,   # Ensure this is included
                      VALIDATE_CERTS = True
                      )

# class EmailSchema(BaseModel):
#     email:List[EmailStr]

async def send_email(email:List[str],instance:User):
    print("welcome to email")
    token_data={"id":instance.user_id,
                "username":instance.username}
    
    token=jwt.encode(token_data,config_credential["SECRET"],algorithm='HS256')
    print(token)

    
    template=f"""
        <!DOCTYPE html>
        <html>
            <head>
            </head>
            <body>
                <div style="display:flex;align-items:center;justify-context:center;flex-direction:column">
                   <h3>Account Verification</h3>
                   <br>
                   <p>Dear User,Please click the button below to verify your account</p>
                   <a style="margin-top:1rem; padding:1rem; border-radius:0.5rem; font-size:1rem;
                    text.decoration:none; background:#0275d8; color: white;" 
                    href="http://localhost:8000/verification/?token={token}">Verify your email</a>
                    <p>Please Kindly ignore this email if you did not register for E-commerce Platform.</p>
                </div>
            </body>
        </html>"""


    message=MessageSchema(subject="E-commmerce Account Verification Email",
                      recipients=email,
                      body=template,
                      subtype="html")

    fm=FastMail(conf)
    await fm.send_message(message=message)


