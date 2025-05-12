# reco_api.py

import os
import datetime
import random
import string
import pymysql
import demo                # demo.py 中包含 main()，用于预热推荐

from typing import List, Dict, Any
from contextlib import contextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import smtplib
from email.mime.text import MIMEText
from email.header import Header

from pydantic import BaseModel, EmailStr
from werkzeug.security import generate_password_hash, check_password_hash

# ──────────────────────────────────────────────────────────────

# 1. 数据库配置（与 demo.py 保持一致，默认端口 3307）
# ──────────────────────────────────────────────────────────────
DB_CONFIG: Dict[str, Any] = dict(
    host="localhost",
    port=3307,
    user="root",
    password="",          # 如有密码请填
    database="buyzu",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor
)

@contextmanager
def db_conn():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

# ──────────────────────────────────────────────────────────────
# 2. FastAPI 基础配置
# ──────────────────────────────────────────────────────────────
app = FastAPI(title="Buyzu API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ──────────────────────────────────────────────────────────────
# 3. SMTP 配置（Google SMTP）
# ──────────────────────────────────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "buyzuec@gmail.com"
SMTP_PASSWORD = "jxigvyjpmzxpxuwj"  # 你的 Google 应用专用密码
EMAIL_FROM    = SMTP_USER

def _send_email(to_email: str, subject: str, content: str):
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From']    = EMAIL_FROM
    msg['To']      = to_email
    msg['Subject'] = Header(subject, 'utf-8')
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM, [to_email], msg.as_string())

# ──────────────────────────────────────────────────────────────
# 4. 工具函数（推荐、商品信息补全等）
# ──────────────────────────────────────────────────────────────
def fallback_hot(k: int) -> List[Dict]:
    sql = """
      SELECT p.productID, p.productName, p.price, p.img, b.brandName
      FROM   products p JOIN brand b USING(brandID)
      ORDER  BY p.sales DESC
      LIMIT  %s
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (k,))
            return cur.fetchall()

def save_to_db(rec_dict: Dict[str, List[int]], algo: str = "mix") -> None:
    sql = """REPLACE INTO recommend_home
             (userKey, productID, rankNo, algoTag, score, createdAt)
             VALUES (%s,%s,%s,%s,%s,%s)"""
    now = datetime.now()
    rows = []
    for uid, pids in rec_dict.items():
        for rank, pid in enumerate(pids, 1):
            rows.append((uid, str(pid), rank, algo, None, now))
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, rows)
            conn.commit()

def recompute_for_user(uid: str, topk: int) -> List[int]:
    sql = "SELECT productID FROM products ORDER BY sales DESC LIMIT %s"
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (topk,))
            return [row["productID"] for row in cur.fetchall()]

def enrich(pid_list: List[int]) -> List[Dict]:
    if not pid_list:
        return []
    fmt = ",".join(["%s"] * len(pid_list))
    sql = f"""
      SELECT p.productID, p.productName, p.price, p.img, b.brandName
      FROM   products p JOIN brand b USING(brandID)
      WHERE  p.productID IN ({fmt})
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(pid_list))
            data = cur.fetchall()
    mapping = {d["productID"]: d for d in data}
    return [mapping[p] for p in pid_list if p in mapping]

# ──────────────────────────────────────────────────────────────
# 5. 模板与静态资源
# ──────────────────────────────────────────────────────────────
templates = Jinja2Templates(directory="static/")

@app.get("/homepage.html", response_class=HTMLResponse)
def serve_home(request: Request):
    demo.main()
    return templates.TemplateResponse("homepage.html", {"request": request})

# ──────────────────────────────────────────────────────────────
# 6. 核心推荐、商品、购物车、邮件接口
# ──────────────────────────────────────────────────────────────
@app.get("/api/home_reco")
def home_reco(request: Request, k: int = 10, refresh: bool = False):
    uid = request.headers.get("X-UserID") or request.cookies.get("SESSIONID")
    algo = "mix"
    if not uid:
        return {"source": "popular", "list": fallback_hot(k)}
    if refresh:
        pids = recompute_for_user(uid, k)
        save_to_db({uid: pids}, algo)
        return {"source": "recomputed", "list": enrich(pids)}
    sql = """
      SELECT r.productID, p.productName, p.price, p.img, b.brandName
      FROM   recommend_home r
      JOIN   products p ON r.productID = p.productID
      LEFT  JOIN brand b ON p.brandID = b.brandID
      WHERE  r.userKey=%s AND r.algoTag=%s
      ORDER  BY r.rankNo
      LIMIT  %s
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (uid, algo, k))
            rows = cur.fetchall()
    if rows:
        return {"source": "cache", "list": rows}
    pids = recompute_for_user(uid, k)
    save_to_db({uid: pids}, algo)
    return {"source": "cold-start", "list": enrich(pids)}

@app.get("/api/product")
def product_detail(id: str):
    sql = """
      SELECT productID, productName, price, descri AS description,
             inventoryCount AS stock, img
      FROM products WHERE productID=%s
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Product not found")
    return {
        "productID": row["productID"],
        "productName": row["productName"],
        "price": float(row["price"]),
        "stock": row["stock"],
        "description": row["description"],
        "images": [row["img"]],
        "reviews": []
    }
'''
def get_owner_key(request: Request) -> str:
    uid = request.headers.get("X-UserID") or request.cookies.get("SESSIONID")
    if not uid:
        raise HTTPException(401, "缺少用户标识")
    return uid
'''
def get_owner_key(request: Request) -> str:
    uid = request.headers.get("X-SessionID") or request.cookies.get("cart_session")
    if not uid:
        raise HTTPException(401, "缺少用户标识")
    return uid

'''
@app.post("/api/cart")
async def add_to_cart(request: Request):
    body = await request.json()
    pid = body.get("id"); qty = int(body.get("qty", 1))
    if not pid or qty < 1:
        raise HTTPException(400, "参数不合法")
    owner = get_owner_key(request)
    sql = """
      INSERT INTO carts(ownerKey, productID, quantity)
      VALUES (%s, %s, %s)
      ON DUPLICATE KEY UPDATE quantity=quantity+VALUES(quantity)
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (owner, pid, qty))
            conn.commit()
    return {"success": True}


@app.get("/api/cart")
async def list_cart(request: Request):
    owner = get_owner_key(request)
    sql = """
      SELECT p.productID,p.productName,p.price,p.img,b.brandName,c.quantity
      FROM carts c
      JOIN products p ON c.productID=p.productID
      LEFT JOIN brand b ON p.brandID=b.brandID
      WHERE c.ownerKey=%s ORDER BY c.createdAt DESC
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (owner,))
            data = cur.fetchall()
    return {"list": data}

@app.delete("/api/cart")
async def delete_cart_item(request: Request, id: str):
    owner = get_owner_key(request)
    sql = "DELETE FROM carts WHERE ownerKey=%s AND productID=%s"
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (owner, id))
            conn.commit()
    return {"success": True}
'''

@app.get("/api/hot_products")
def hot_products(k: int = 8):
    sql = """
      SELECT p.productID,p.productName,p.price,p.img,b.brandName
      FROM products p
      LEFT JOIN brand b ON p.brandID=b.brandID
      ORDER BY p.sales DESC LIMIT %s
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (k,))
            return {"list": cur.fetchall()}

class EmailRequest(BaseModel):
    email: EmailStr
    subject: str = "来自 Buyzu 的问候"
    body: str

@app.post("/api/send_email")
async def api_send_email(req: EmailRequest):
    try:
        _send_email(req.email, req.subject, req.body)
        return {"success": True, "message": f"邮件已发送至 {req.email}"}
    except Exception as e:
        raise HTTPException(500, f"发送邮件失败: {e}")

class SubscribeRequest(BaseModel):
    email: EmailStr

@app.post("/api/subscribe")
async def api_subscribe(req: SubscribeRequest):
    try:
        _send_email(
            req.email,
            "感谢订阅 Buyzu",
            "欢迎加入 Buyzu 邮件列表！您将第一时间收到最新趋势与优惠信息。"
        )
        return {"success": True, "message": f"欢迎邮件已发送至 {req.email}"}
    except Exception as e:
        raise HTTPException(500, f"发送欢迎邮件失败: {e}")

# ──────────────────────────────────────────────────────────────
# 7. 用户系统：验证码、注册、登录、重置密码、Google OAuth、管理员创建
# ──────────────────────────────────────────────────────────────

VERIF_CODE_LEN    = 6
VERIF_EXPIRY_MIN  = 10
GOOGLE_CLIENT_ID  = "YOUR_GOOGLE_CLIENT_ID"

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=VERIF_CODE_LEN))

class VerifReq(BaseModel):
    email: EmailStr

@app.post("/api/send-verification")
async def send_verification(req: VerifReq):
    code = generate_verification_code()
    expiry = datetime.now() + timedelta(minutes=VERIF_EXPIRY_MIN)
    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM verification_codes WHERE email=%s", (req.email,))
                cur.execute(
                    "INSERT INTO verification_codes(email,code,expiry_time) VALUES(%s,%s,%s)",
                    (req.email, code, expiry)
                )
            conn.commit()
        body = f"""Dear User,

Your verification code is: {code}

It expires in {VERIF_EXPIRY_MIN} minutes.
If you didn't request this, please ignore."""
        _send_email(req.email, "Buyzu Registration Verification Code", body)
        return {"message": "Verification code sent"}
    except Exception as e:
        raise HTTPException(500, f"发送验证码失败: {e}")

class RegisterReq(BaseModel):
    username: str
    password: str
    email: EmailStr
    verificationCode: str

@app.post("/api/register")
async def register(req: RegisterReq):
    if not all([req.username, req.password, req.email, req.verificationCode]):
        raise HTTPException(400, "所有字段均为必填")
    try:
        # 验证码校验
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                  "SELECT code,expiry_time FROM verification_codes WHERE email=%s ORDER BY expiry_time DESC LIMIT 1",
                  (req.email,)
                )
                row = cur.fetchone()
        if not row or row["code"] != req.verificationCode:
            raise HTTPException(400, "验证码无效或不存在")
        if row["expiry_time"] < datetime.now():
            raise HTTPException(400, "验证码已过期")

        # 用户名/邮箱唯一
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE username=%s", (req.username,))
                if cur.fetchone():
                    raise HTTPException(400, "用户名已存在")
                cur.execute("SELECT id FROM users WHERE email=%s", (req.email,))
                if cur.fetchone():
                    raise HTTPException(400, "邮箱已注册")
                hashed = generate_password_hash(req.password)
                cur.execute(
                    "INSERT INTO users(username,password,email) VALUES(%s,%s,%s)",
                    (req.username, hashed, req.email)
                )
            conn.commit()
        # 删除验证码
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM verification_codes WHERE email=%s", (req.email,))
            conn.commit()
        return {"message": "注册成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"注册失败: {e}")

class LoginReq(BaseModel):
    username: str
    password: str

@app.post("/api/login")
async def login(req: LoginReq):
    if not req.username or not req.password:
        raise HTTPException(400, "用户名和密码为必填")
    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                  "SELECT id,username,password FROM users WHERE username=%s",
                  (req.username,)
                )
                user = cur.fetchone()
        if not user or not check_password_hash(user["password"], req.password):
            raise HTTPException(401, "用户名或密码错误")
        return {"message": "登录成功", "user": {"id": user["id"], "username": user["username"]}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"登录失败: {e}")

class GoogleAuthReq(BaseModel):
    token: str
'''
@app.post("/api/auth/google")
async def google_auth(req: GoogleAuthReq):
    if not req.token:
        raise HTTPException(400, "Token 未提供")
    try:
        idinfo = id_token.verify_oauth2_token(
            req.token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        google_id = idinfo["sub"]
        email     = idinfo["email"]
        name      = idinfo.get("name", email.split("@")[0])
        # 查询或创建
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id,username FROM users WHERE google_id=%s", (google_id,))
                user = cur.fetchone()
                if not user:
                    cur.execute(
                      "INSERT INTO users(username,email,google_id) VALUES(%s,%s,%s)",
                      (name, email, google_id)
                    )
                    conn.commit()
                    cur.execute("SELECT id,username FROM users WHERE google_id=%s", (google_id,))
                    user = cur.fetchone()
        return {"message": "登录成功", "user": {"id": user["id"], "username": user["username"]}}
    except ValueError:
        raise HTTPException(401, "Invalid token")
    except Exception as e:
        raise HTTPException(500, f"Google 登录失败: {e}")
'''
@app.get("/create-admin")
async def create_admin():
    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE username='admin'")
                if cur.fetchone():
                    raise HTTPException(400, "Admin 用户已存在")
                hashed = generate_password_hash("123")
                cur.execute(
                  "INSERT INTO users(username,password,email) VALUES('admin',%s,'admin@example.com')",
                  (hashed,)
                )
            conn.commit()
        return {"message": "Admin 用户创建成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"创建 Admin 失败: {e}")

@app.post("/api/send-reset-code")
async def send_reset_code(req: VerifReq):
    # 与 send-verification 相同逻辑，但检查邮箱存在
    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email=%s", (req.email,))
                if not cur.fetchone():
                    raise HTTPException(404, "邮箱未注册")
        return await send_verification(req)  # 复用发送验证码
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"发送重置码失败: {e}")

class ResetPwdReq(BaseModel):
    email: EmailStr
    verificationCode: str
    newPassword: str

@app.post("/api/reset-password")
async def reset_password(req: ResetPwdReq):
    if not all([req.email, req.verificationCode, req.newPassword]):
        raise HTTPException(400, "所有字段为必填")
    try:
        # 验证码校验
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                  "SELECT code,expiry_time FROM verification_codes WHERE email=%s ORDER BY expiry_time DESC LIMIT 1",
                  (req.email,)
                )
                row = cur.fetchone()
        if not row or row["code"] != req.verificationCode:
            raise HTTPException(400, "验证码无效或不存在")
        if row["expiry_time"] < datetime.now():
            raise HTTPException(400, "验证码已过期")
        # 重置密码
        hashed = generate_password_hash(req.newPassword)
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET password=%s WHERE email=%s", (hashed, req.email))
                if cur.rowcount == 0:
                    raise HTTPException(404, "用户未找到")
                cur.execute("DELETE FROM verification_codes WHERE email=%s", (req.email,))
            conn.commit()
        return {"message": "密码重置成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"重置密码失败: {e}")

# ──────────────────────────────────────────────────────────────
# 8. 静态资源挂载（放在所有 API 路由之后，避免 404）
# ──────────────────────────────────────────────────────────────
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/product.html")
async def serve_product():
    return FileResponse("static/product.html")

@app.get("/cart.html")
async def serve_cart():
    return FileResponse("static/cart.html")

@app.get("/checkout.html")
async def serve_checkout():
    return FileResponse("static/checkout.html")