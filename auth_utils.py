from passlib.context import CryptContext
from datetime import datetime, timezone

# 告诉 Passlib 用哪个算法来加密密码（本项目用 bcrypt）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 注册时用，明文 → bcrypt 哈希
def hash_password(plain_password: str) -> str:
    """明文密码 -> 哈希密码"""
    return pwd_context.hash(plain_password)


# 登录时用，验证密码是否匹配
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证 明文密码 和 哈希密码 是否匹配"""
    return pwd_context.verify(plain_password, hashed_password)


from jose import JWTError, jwt
from datetime import timedelta
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


# 生成 JWT 的函数，登录成功后会用到
def create_access_token(data: dict) -> str:
    """生成 JWT"""
    to_encode = data.copy()  # 把传进来的字典复制一份，不直接修改原始 data
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )  # 计算过期时间，datetime.now(timezone.utc) 获取当前 UTC 时间，timedelta 加上过期分钟数
    to_encode.update(
        {"exp": expire}
    )  # 把过期时间加进字典，exp 是 JWT 标准规定的字段名，python-jose 会自动把它转成 Unix 时间戳写进 Payload。
    return jwt.encode(
        to_encode, SECRET_KEY, algorithm=ALGORITHM
    )  # 生成 JWT，传入要编码的数据、密钥和算法。encode用于将数据转换成 JWT 格式。


# 内部过程：
# ① Header = {"alg": "HS256", "typ": "JWT"} → Base64Url
# ② Payload = to_encode → Base64Url
# ③ Signature = HMAC_SHA256(① + "." + ②, SECRET_KEY)
# ④ 拼接返回 "eyJ....eyJ....Sfl..."

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)  # 告诉 FastAPI 登录接口的 URL，FastAPI 会自动在 Swagger 文档里生成一个输入框，让用户输入 JWT。


# 用户认证依赖函数
def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    # 定义一个通用的认证失败异常，后面验证过程中如果任何一步失败都抛这个异常，避免泄露过多信息。
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:  # 验证 JWT，解密出 payload,从 payload 里取出用户名，然后查数据库拿到用户对象。
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )  # python-jose 在这一行同时做了三件事：验签、检查过期、解码 Payload。任何一个失败都会抛 JWTError，被 except 捕获返回 401。
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except (
        JWTError
    ):  # JWT 解密失败，可能是因为 token 无效、过期或者被篡改了，这时抛出认证失败异常。
        raise credentials_exception

    # 从数据库查用户，如果用户不存在，抛出认证失败异常；如果用户存在，返回用户对象。
    from models import User

    user = (
        db.query(User).filter(User.username == username).first()
    )  # Token 里存的是用户名，直接用于查询。
    if (
        user is None
    ):  # 正常情况下 sub 一定有值，但防御性地检查一下。如果用户不存在，可能是因为用户被删除了，这时也抛出认证失败异常。
        raise credentials_exception

    # 认证成功，返回用户对象
    return user
