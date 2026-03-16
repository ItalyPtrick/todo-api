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
