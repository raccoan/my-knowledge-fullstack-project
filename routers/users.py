from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from starlette.responses import JSONResponse

from database import get_db
from schemas.user import User, LoginRequest,RegisterRequest,ResetPasswordRequest
from models.user import User as UserModel

from utils.password import hash_password,verify_password

from utils.jwt import create_token
from utils.auth import  get_current_user
from utils.verification import verify_code


router = APIRouter()



# 登录接口
@router.post('/login')
def login(
    user: LoginRequest,
    db: Session = Depends(get_db)
):
    db_user = (
        db.query(UserModel)
        .filter(
            UserModel.username == user.username
        )
        .first()
    )

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )

    if not verify_password(
        user.password,
        db_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )

    token = create_token(
        {
            "user_id": db_user.id
        }
    )

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
    # 1. 检查验证码类型
    if user.code_type not in ["email", "phone"]:
        raise HTTPException(
            status_code=400,
            detail="验证码类型错误"
        )

    # 2. 根据验证码类型确定注册目标
    if user.code_type == "email":
        if not user.email:
            raise HTTPException(
                status_code=400,
                detail="邮箱不能为空"
            )

        target = user.email

    else:
        if not user.phone:
            raise HTTPException(
                status_code=400,
                detail="手机号不能为空"
            )

        target = user.phone

    # 3. 验证验证码
    verify_result = verify_code(
        db=db,
        target=target,
        code=user.code,
        code_type=user.code_type
    )

    if verify_result == "expired":
        raise HTTPException(
            status_code=400,
            detail="验证码已过期，请重新获取"
        )

    if verify_result == "invalid":
        raise HTTPException(
            status_code=400,
            detail="验证码错误，请重新输入"
        )

    # 4. 检查用户名是否已经注册
    existing_username = (
        db.query(UserModel)
        .filter(
            UserModel.username == user.username
        )
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="用户名已存在，请更换一个"
        )

    # 5. 检查邮箱是否已经注册
    if user.email:
        existing_email = (
            db.query(UserModel)
            .filter(
                UserModel.email == user.email
            )
            .first()
        )

        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="该邮箱已注册，请直接登录"
            )

    # 6. 检查手机号是否已经注册
    if user.phone:
        existing_phone = (
            db.query(UserModel)
            .filter(
                UserModel.phone == user.phone
            )
            .first()
        )

        if existing_phone:
            raise HTTPException(
                status_code=400,
                detail="该手机号已注册，请直接登录"
            )

    # 7. 密码加密
    hashed_password = hash_password(
        user.password
    )

    # 8. 创建用户
    db_user = UserModel(
        username=user.username,
        password=hashed_password,
        email=user.email,
        phone=user.phone
    )

    db.add(db_user)

    try:
        db.commit()
        db.refresh(db_user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="用户名、邮箱或手机号已被注册"
        )

    return {
        "message": "注册成功"
    }


@router.post('/reset-password')
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    # 1. 查找邮箱对应的用户
    db_user = (
        db.query(UserModel)
        .filter(
            UserModel.email == request.email
        )
        .first()
    )

    if not db_user:
        raise HTTPException(
            status_code=400,
            detail="该邮箱未注册"
        )

    # 2. 验证验证码
    verify_result = verify_code(
        db=db,
        target=request.email,
        code=request.code,
        code_type="reset_password"
    )

    if verify_result == "expired":
        raise HTTPException(
            status_code=400,
            detail="验证码已过期，请重新获取"
        )

    if verify_result == "invalid":
        raise HTTPException(
            status_code=400,
            detail="验证码错误，请重新输入"
        )

    # 3. 修改密码
    db_user.password = hash_password(
        request.password
    )

    db.commit()

    return {
        "message": "密码修改成功"
    }


