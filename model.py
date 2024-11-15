from tortoise import Model,fields
from tortoise.contrib.pydantic import pydantic_model_creator
from datetime import datetime
from pydantic import BaseModel


class User(Model):
    user_id=fields.IntField(pk=True,index=True)
    username=fields.CharField(max_length=20,null=False,unique=True)
    email=fields.CharField(max_length=50,null=False,unique=True)
    password=fields.CharField(max_length=100,null=False)
    is_verified=fields.BooleanField(default=False)
    join_date=fields.DatetimeField(default=datetime.utcnow)
  

class Business(Model):
    business_id=fields.IntField(pk=True,index=True)
    business_name=fields.CharField(max_length=20,null=False,unique=True)
    location=fields.CharField(max_length=100,null=False,default="unspecified")
    description=fields.TextField(null=True)
    logo=fields.CharField(max_length=200,null=False,default="default.jpg")
    owner=fields.ForeignKeyField("model.User",related_name="business")

class Product(Model):
    product_id=fields.IntField(pk=True,index=True)
    product_name=fields.CharField(max_length=100,null=False,index=True)
    category=fields.CharField(max_length=50,index=True)
    price=fields.DecimalField(max_digits=12,decimal_places=2)
    after_discount_price=fields.DecimalField(max_digits=12,decimal_places=2)
    discount_percentage=fields.IntField()
    offer_upto=fields.DateField(default=datetime.utcnow)
    product_image=fields.CharField(max_length=200,null=False,default="product.jpg")
    date_published=fields.DatetimeField(default=datetime.utcnow)
    business=fields.ForeignKeyField("model.Business",related_name="product")

user_pydantic=pydantic_model_creator(User,name="User",exclude=("is_verified", ))
user_pydanticIn=pydantic_model_creator(User,name="UserIn",exclude_readonly=True,exclude=("is_verified", "join_date"))
user_pydanticOut=pydantic_model_creator(User,name="UserOut",exclude=("password", ))

business_pydantic=pydantic_model_creator(Business,name="Bussiness")
business_pydanticIn=pydantic_model_creator(Business,name="BusinessIn",exclude=("logo","business_id"))

product_pydantic=pydantic_model_creator(Product,name="Product")
product_pydanticIn=pydantic_model_creator(Product,name="ProductIn",exclude=("discount_percentage","product_id","product_image","date_published"))










