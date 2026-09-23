from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from database import get_db
from schemas.user import User, LoginRequest,RegisterRequest
from models.user import User as UserModel

from utils.password import hash_password,verify_password

from utils.jwt import create_token
from utils.auth import  get_current_user
router = APIRouter()


# 注册接口
@router.post('/register')
def register(
    user:User,
    db:Session = Depends(get_db)
):
    #查询是否存在该用户
    exist_user = db.query(UserModel).filter(UserModel.username==user.username).first()
    if exist_user:
        return JSONResponse({"message": f"{UserModel.username}已存在"})

    #密码加密
    hashed_password =  hash_password(user.password)

    # 创建数据库对象
    new_user = UserModel(
        username = user.username,
        age = user.age,
        password = hashed_password
                         )
    # 保存数据库
    db.add(new_user)
    db.commit()
    db.refresh(
        new_user
    )
    return {
        JSONResponse({"message":"注册成功",
                    "user":{
                        "username":new_user.username,
                        "age":new_user.age
                    }


                      })
    }

# 登录接口
@router.post('/login')
def login(
    user:LoginRequest,
    db:Session = Depends(get_db)
):
    db_user = db.query(UserModel).filter(UserModel.username == user.username).first()
    if not db_user:
        return {"message":"该用户不存在"}
    if not verify_password(
        user.password,
        db_user.password
    ):
        return {"message":"密码错误"}
    print("数据库查询到的用户:", db_user.id, db_user.username)

    # print("登录用户:", user.id, user.username)
    token = create_token({
        "id":db_user.id,
        "username":db_user.username
    })

    return {
        "message": "登录成功",
        "token": token,
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "phone": db_user.phone
        }
    }



@router.get('/')
def hello():
    return {
        "message": "hello fastapi"
    }

@router.get('/users')
def get_users(
        db:Session=Depends(get_db),
        current_user=Depends(get_current_user)
        ):
    users = db.query(UserModel).all()
    return users

@router.get('/users/{user_id}')
def get_user(
        user_id:int,
        db:Session = Depends(get_db)
):

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        return JSONResponse({"message": "user not found"}, 404)
    return user

@router.post('/users')
def add_user(user:User,db:Session = Depends(get_db)):
    db_user = UserModel(age=user.age,username=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return JSONResponse({"message":f"user {db_user.name} added successfully"})

@router.delete('/users/{user_id}')
def delete_user(user_id:int,db:Session =Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        return  JSONResponse({"message":f"userId {user_id} not found"})
    db.delete(user)
    db.commit()
    return JSONResponse({"message":f"user {user.name} deleted successfully"})

@router.put('/users/{user_id}')
def update_user(user_id:int,user:User,db:Session = Depends(get_db)):

    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not db_user:
        return JSONResponse({"message":f"user {user_id} not found"})
    db_user.name = user.name
    db_user.age = user.age
    db.commit()
    db.refresh(db_user)
    return JSONResponse({"message":f"{user}update successfully"})

@router.post('/register')
def register(
    user: RegisterRequest,
    db: Session = Depends(get_db)
):
    # 1. 检查用户名
    exist_user = (
        db.query(UserModel)
        .filter(
            UserModel.username == user.username
        )
        .first()
    )

    if exist_user:
        return JSONResponse(
            status_code=400,
            content={
                "message": "用户名已存在"
            }
        )

    # 2. 检查邮箱
    exist_email = (
        db.query(UserModel)
        .filter(
            UserModel.email == user.email
        )
        .first()
    )

    if exist_email:
        return JSONResponse(
            status_code=400,
            content={
                "message": "邮箱已被注册"
            }
        )

    # 3. 检查手机号
    exist_phone = (
        db.query(UserModel)
        .filter(
            UserModel.phone == user.phone
        )
        .first()
    )

    if exist_phone:
        return JSONResponse(
            status_code=400,
            content={
                "message": "手机号已被注册"
            }
        )

    # 4. 密码加密
    hashed_password = hash_password(
        user.password
    )

    # 5. 创建用户
    new_user = UserModel(
        username=user.username,
        email=user.email,
        phone=user.phone,
        password=hashed_password
    )

    # 6. 保存数据库
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 7. 返回注册结果
    return JSONResponse(
        status_code=201,
        content={
            "message": "注册成功",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "phone": new_user.phone
            }
        }
    )


