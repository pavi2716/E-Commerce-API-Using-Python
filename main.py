from fastapi import FastAPI,Request,HTTPException,status,Depends 
from tortoise.exceptions import IntegrityError
from tortoise.contrib.fastapi import register_tortoise
from model import *
from authentication import *
from fastapi.security import OAuth2PasswordBearer,OAuth2PasswordRequestForm
#signals
from tortoise.signals import post_save
from typing import List,Optional,Type
from tortoise import BaseDBAsyncClient
from email_utils import *
#response email
from fastapi.responses import HTMLResponse
#templates
from fastapi.templating import Jinja2Templates
#image upload
from fastapi import File,UploadFile
import secrets
from fastapi.staticfiles import StaticFiles
from PIL import Image


app=FastAPI(title="E-commerce")

register_tortoise(app,db_url="sqlite://database.sqlite3",modules={"model":["model"]},generate_schemas=True,add_exception_handlers=True)


app.mount("/static",StaticFiles(directory="static"),name="static")

@app.get('/')
def homepage():
    return["Welcome to our e-commerce platform!","Explore our collection and enjoy shopping from the comfort of your home."]


@app.post('/registration')
async def user_registration(user:user_pydanticIn):
    user_info=user.dict(exclude_unset=True)
    print("user_info",user_info)
    user_info["password"]=hashed_password(user_info["password"])

   

    if await User.exists(email=user_info["email"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exit")
    
    if await User.exists(username=user_info["username"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    try:
        user_obj=await User.create(**user_info)
        print("register", user_obj)
        new_user=await user_pydantic.from_tortoise_orm(user_obj)
        print("register new user",new_user )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    return {"status":"completed","data":f"Hello{new_user.username},Thanks for choosing our E-commerce platform!.Please check your email inbox and click the below link to confirm your registration."}


@post_save(User)
async def create_business(sender:"Type[User]",instance:User,
                          created:bool,using_db:"Optional[BaseDBAsyncClient]",
                          update_fields:List[str])->None:
    print("business")
    
    if created:
        business_obj=await Business.create(business_name=instance.username,owner=instance)
        print(" business created")
        await  business_pydantic.from_tortoise_orm(business_obj)
        await send_email([instance.email],instance)



templates=Jinja2Templates(directory="templates")

@app.get('/verification',response_class=HTMLResponse)
async def email_verification(request:Request,token:str):
    user=await verify_token(token)
    print("verification email",user)
    if user and not user.is_verified:
        user.is_verified=True
        await user.save()
        return templates.TemplateResponse("verification.html",
                                          {"request":request,"username":user.username})

    else:
        print("invalid error")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token",
                            headers={"WWW-Authenticate": "Bearer"})


oath2_schema=OAuth2PasswordBearer(tokenUrl='token')
print("oath2_schema",oath2_schema)


@app.post('/token')
async def generate_token(request_form:OAuth2PasswordRequestForm=Depends()):
    token=await token_generator(request_form.username,request_form.password)
    print("token")
    return {"access_token":token,"token_type":"bearer"}


async def get_current_user(token:str=Depends(oath2_schema)):
    try:
        payload=jwt.decode(token,config_credential['SECRET'],algorithms=["HS256"])
        print("payload decode",payload)
        user=await User.get(user_id=payload.get("id"))
        
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid username or password",
                            headers={"WWW.Authenticate": "Bearer"})
    return await user



@app.post('/user/me')
async def user_login(user:user_pydanticIn=Depends(get_current_user)):
    business=await Business.get(owner=user)
    logo=business.logo #23rg67.png
    logo_path="localhost:8000/static/images/" + logo
    join_date = user.join_date 
    return {"status":"ok",
            "data":{"username":user.username,
                    "email":user.email,
                    "verified":user.is_verified,
                    "joined_date":user.join_date.strftime('%b %d, %y'),
                    "logo":logo_path}}

@app.post("/uploadfile/profile")
async def create_upload_file(file:UploadFile=File(...),user:user_pydantic=Depends(get_current_user)):
    FILEPATH="./static/images/"
    filename=file.filename
    #test.png>>["test","png"]
    extension=filename.split(".")[1]

    if extension not in ["png","jpg","jpeg"]:
        return{"status":"error","detail":"File should be in png or jpg or jpeg format"}
    
    #./static/images/u45jkl568g.png
    token_name=secrets.token_hex(10) + "." + extension
    generated_name=FILEPATH + token_name
    file_content=await file.read()

    with open(generated_name,"wb") as file:
        file.write(file_content)

    img=Image.open(generated_name)
    img=img.resize(size=(200,200))
    img.save(generated_name)
    file.close()

    business=await Business.get(owner=user)
    owner=await business.owner
    if owner==user:
        business.logo=token_name
        await business.save()
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticate to perform this action",
                            headers={"WWW.Authenticate":"Bearer"})
    file_url="localhost:8000" + generated_name[1:]
    return{"status":"uploaded","filename":file_url}


@app.put("/business/{business_id}")
async def update_business(business_id:int,update_business:business_pydanticIn,user:user_pydantic=Depends(get_current_user)):
    update_business=update_business.dict()
    business=await Business.get(business_id=business_id)
    business_owner=await business.owner
    
    if user==business_owner:
        await business.update_from_dict(update_business)
        await business.save()
        response=await business_pydantic.from_tortoise_orm(business)
        return{"status":"business updated","data":response}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticate to perform this action",
                            headers={"WWW.Authenticate":"Bearer"})


#CRUD Functionality
@app.post("/products")
async def add_product(product:product_pydanticIn,user:user_pydantic=Depends(get_current_user)):
    product=product.dict(exclude_unset=True)

    if product["price"]>0:
        product["discount_percentage"]=((product["price"]-product["after_discount_price"])/product["price"])*100
        business = await Business.get(owner=user)  # Fetch the business associated with the user

        if business:  # Check if the business exists
            product_obj=await Product.create(**product,business=business)
            product_obj=await product_pydantic.from_tortoise_orm(product_obj)
            return{"status":"ok","data":product_obj}
        else:
            return {"status": "error", "message": "No business associated with this user"}
        
    else:
        return{"status":"error"}



@app.post("/uploadfile/product/{product_id}")
async def create_upload_file(product_id:int,file:UploadFile=File(...),user:user_pydantic=Depends(get_current_user)):
    FILEPATH="./static/images/"
    filename=file.filename
    extension=filename.split(".")[1]

    if extension not in ["png","jpg","jpeg"]:
        return{"status":"error","detail":"File should be in png or jpg or jpeg format"}
    
    #./static/images/u45jkl568g.png
    token_name=secrets.token_hex(10) + "." + extension
    generated_name=FILEPATH + token_name
    file_content=await file.read()

    with open(generated_name,"wb") as file:
        file.write(file_content)

    img=Image.open(generated_name)
    img=img.resize(size=(200,200))
    img.save(generated_name)
    file.close()

    product=await Product.get(product_id=product_id)
    business=await product.business
    owner=await business.owner

    if owner==user:
        product.product_image=token_name
        await product.save()
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticate to perform this action",
                            headers={"WWW.Authenticate":"Bearer"})
    file_url="localhost:8000" + generated_name[1:]
    return{"status":"uploaded","filename":file_url}


@app.get("/product")
async def get_product():
    response=await product_pydantic.from_queryset(Product.all())
    return{"status":"ok","data":response}



@app.get("/product/{product_id}")
async def get_product(product_id:int):
    product=await Product.get(product_id=product_id)
    business=await product.business
    owner=await business.owner
    response=await product_pydantic.from_queryset_single(Product.get(product_id=product_id))
    return{"status":"ok","data":{"product_details":response,
                                 "business_details":{"name":business.business_name,
                                                     "location":business.location,
                                                     "decription":business.description,
                                                     "logo":business.logo,
                                                     "owner_id":owner.user_id,
                                                     "business_id":business.business_id,
                                                     "email":owner.email,
                                                     "join_date":owner.join_date.strftime("%b %d %y")}}}




@app.delete("/products/{product_id}")
async def delete_product(product_id:int,user:user_pydantic=Depends(get_current_user)):
    product=await Product.get(product_id=product_id)
    business=await product.business
    owner=await business.owner

    if user==owner:
        await product.delete()
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticate to perform this action",
                            headers={"WWW.Authenticate":"Bearer"})
    return{"status":"deleted"}

#update
@app.put("/product/{product_id}")
async def update_product(product_id:int,update_info:product_pydanticIn,user:user_pydantic=Depends(get_current_user)):
    product=await Product.get(product_id=product_id)
    business=await product.business 
    owner=await business.owner

    update_info=update_info.dict(exclude_unset=True)
    update_info["date_published"]=datetime.utcnow()

    if user==owner and update_info["price"]!=0:
        update_info["discount_percentage"]=((update_info["price"]-update_info["after_discount_price"])/update_info["price"])*100
        product=await product.update_from_dict(update_info)
        await product.save()
        response=await product_pydantic.from_tortoise_orm(product)
        return{"status":"updated","data":response}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticate to perform this action or invalid user input",
                            headers={"WWW.Authenticate":"Bearer"})
    
