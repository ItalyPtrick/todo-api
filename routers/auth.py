from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserCreate, UserResponse, Token
from auth_utils import hash_password, verify_password, create_access_token

# prefix="/auth" — 这个路由下所有接口都以 /auth 开头，所以注册接口完整路径是 /auth/register
# tags=["auth"] — Swagger 文档里分组显示用
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
        )

    # 创建新用户
    new_user = User(
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        # 注意：存进数据库的是 hashed_password，
        # 明文 user_data.password 永远不碰数据库。
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


from schemas import UserCreate, UserResponse, Token
from auth_utils import hash_password, verify_password, create_access_token


# 登录接口，验证用户名和密码，成功后返回 JWT
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  # OAuth2PasswordBearer 是 OAuth2 标准的实现，OAuth2 标准规定：登录接口必须接收表单格式，不能是 JSON。
    db: Session = Depends(get_db),
):
    # 查用户
    user = db.query(User).filter(User.username == form_data.username).first()
    if (
        not user
    ):  # 如果用户不存在，直接报错，不要告诉用户是用户名错了还是密码错了，增加安全性
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(
        form_data.password, user.hashed_password
    ):  # verify_password() 会把用户输入的明文密码和数据库里的哈希密码进行对比，验证成功返回 True，否则返回 False。
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    # 生成 Token
    token = create_access_token(
        data={"sub": str(user.id)}
    )  # JWT 的 payload 里通常会放一个 "sub" 字段，代表这个 token 是给哪个用户的。这里放用户的 id，前端以后需要这个 id 来区分不同用户的数据。
    return {
        "access_token": token,
        "token_type": "bearer",
    }  # 这里的 token_type 是 OAuth2 的规范，虽然我们这个项目不完全符合 OAuth2，但也照着这个格式返回，方便前端使用。
