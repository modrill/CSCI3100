# reco_api.py

import os
import datetime
import random
import string
import pymysql
import demo                # demo.py 中包含 main()，用于预热推荐

from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from datetime import datetime, timedelta

import uuid
from fastapi import Body
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi import HTTPException, Request, status
import smtplib
from email.mime.text import MIMEText
from email.header import Header

from pydantic import BaseModel, EmailStr
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from typing import List, Dict, Any

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
# 4. 管理员简单认证中间件（兼容之前前端用 ADMIN_TOKEN='admin-token'）
# ──────────────────────────────────────────────────────────────
ADMIN_TOKEN = "admin-token"

async def admin_required(request: Request):
    authorization = request.headers.get("Authorization")
    if authorization != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="需要管理员权限")

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
             (userID, productID, rankNo, algoTag, score, createdAt)
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
async def serve_home(request: Request):
    # 1) 预热 demo 推荐（保持原有逻辑）
    demo.main()

    # 2) 读取当前用户购物车
    try:
        user_id = get_owner_key(request)
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                  SELECT 
                    p.productID,
                    p.productName,
                    p.price,
                    p.img,
                    b.brandName,
                    c.quantity
                  FROM carts c
                  JOIN products p ON c.productID = p.productID
                  LEFT JOIN brand b ON p.brandID = b.brandID
                  WHERE c.userID = %s
                  ORDER BY c.createdAt DESC
                """, (user_id,))
                cart_items = cur.fetchall()
    except HTTPException:
        # 未登录或 header 缺失，则不报错，只返回空列表
        cart_items = []

    # 3) 调用现有的 home_reco 接口获取推荐列表
    #    利用 fastapi 内部调用，直接传入 request
    reco_resp = await home_reco(request, k=8, refresh=False)
    print("reco_resp")
    print(reco_resp)
    reco_list = reco_resp.get("list", [])

    # 4) 渲染模板，带上 cart_items 和 reco_list
    return templates.TemplateResponse(
      "homepage.html",
      {
        "request": request,
        "cartItems": cart_items,
        "recoList": reco_list
      }
    )
# ──────────────────────────────────────────────────────────────
# 6. 核心推荐、商品、购物车、邮件接口
# ──────────────────────────────────────────────────────────────
@app.get("/api/home_reco")
async def home_reco(request: Request, k: int = 8, refresh: bool = False):
    """
    基于 userID（session）获取首页推荐：
      - 未登录：popular
      - refresh=True：recomputed
      - 已缓存：cache
      - 冷启动：cold-start
    """
    try:
        user_id = get_owner_key(request)
    except HTTPException:
        # 未登录，返回热门
        print("NO NO NO")
        return {"source": "popular", "list": fallback_hot(k)}

    algo = "mix"

    # 强制重新计算
    if refresh:
        pids = recompute_for_user(user_id, k)
        save_to_db({user_id: pids}, algo)
        return {"source": "recomputed", "list": enrich(pids)}

    # 尝试从缓存取
    sql = """
      SELECT r.productID, p.productName, p.price, p.img, b.brandName
      FROM   recommend_home r
      JOIN   products p ON r.productID = p.productID
      LEFT  JOIN brand b ON p.brandID = b.brandID
      WHERE  r.userID = %s
        AND  r.algoTag = %s
      ORDER  BY r.rankNo
      LIMIT  %s
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, algo, k))
            rows = cur.fetchall()

    if rows:
        return {"source": "cache", "list": rows}

    # 冷启动
    pids = recompute_for_user(user_id, k)
    save_to_db({user_id: pids}, algo)
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
def get_owner_key(request: Request) -> int:
    """
    必须登录才能操作购物车，
    从请求头 X-UserID 获取用户 ID（int）
    """
    print(request.headers)
    user_id = request.headers.get("X-UserID") or request.headers.get("x-userid")
    print(f">>> DEBUG: Received X-UserID header = {user_id!r}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要在请求头中提供 X-UserID"
        )
    try:
        return int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-UserID 必须是整数"
        )
# ──────────────────────────────────────────────────────────────
# 4. 购物车相关接口
# ──────────────────────────────────────────────────────────────

class CartItem(BaseModel):
    id: str
    qty: int

@app.post("/api/cart", status_code=201, summary="添加到购物车")
async def add_to_cart(item: CartItem, request: Request):
    print(">>> add_to_cart called")
    user_id = get_owner_key(request)
    print(f"add_to_cart: user={user_id}, item={item.id}, qty={item.qty}")
    if item.qty < 1:
        raise HTTPException(400, "数量必须至少为 1")

    # 1) 检查商品是否存在及库存
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT inventoryCount FROM products WHERE productID=%s", (item.id,))
            prod = cur.fetchone()
    if not prod:
        raise HTTPException(404, "Product not found")
    if item.qty > prod["inventoryCount"]:
        raise HTTPException(400, f"库存不足，仅剩 {prod['inventoryCount']}")

    # 2) 写入购物车
    sql = """
      INSERT INTO carts(userID, productID, quantity)
      VALUES (%s, %s, %s)
      ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
    """
    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (user_id, item.id, item.qty))
            conn.commit()
    except pymysql.MySQLError as e:
        raise HTTPException(500, f"数据库错误: {e}")

    return {"success": True}

@app.put("/api/cart", summary="更新购物车商品数量")
async def update_cart_item(request: Request, item: CartItem):
    user_id = get_owner_key(request)
    if item.qty < 1:
        raise HTTPException(status_code=400, detail="数量必须至少为 1")

    sql = """
      UPDATE carts
         SET quantity = %s
       WHERE userID = %s AND productID = %s
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (item.qty, user_id, item.id))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="购物车中无此商品")
            conn.commit()
    return {"success": True}

@app.get("/api/cart", summary="列出当前用户购物车所有商品")
async def list_cart(request: Request):
    print(request.headers.get('X-UserID'), request.headers.get('x-userid'))

    user_id = get_owner_key(request)

    sql = """
      SELECT
        p.productID,
        p.productName,
        p.price,
        p.img,
        b.brandName,
        c.quantity
      FROM carts c
      JOIN products p ON c.productID = p.productID
      LEFT JOIN brand b ON p.brandID = b.brandID
      WHERE c.userID = %s
      ORDER BY c.createdAt DESC
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            data = cur.fetchall()
    return {"list": data}

@app.delete("/api/cart", summary="从购物车删除某个商品")
async def delete_cart_item(request: Request, id: str):
    user_id = get_owner_key(request)

    sql = "DELETE FROM carts WHERE userID = %s AND productID = %s"
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, id))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="购物车中无此商品")
            conn.commit()
    return {"success": True}


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

# 在 "6. 核心推荐、商品、购物车、邮件接口" 区域添加以下路由
@app.get("/api/search", summary="搜索商品")
async def search_products(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    sort: str    = Query("sales_desc", description="排序方式：sales_desc/price_asc/price_desc/sales_asc")
) -> Dict[str, List[Dict[str, Any]]]:
    # 基本 SQL
    base_sql = """
      SELECT
        p.productID   AS id,
        p.productName AS name,
        p.price       AS price,
        p.img         AS image_url,
        p.sales       AS sales,
        p.rating      AS rating,
        b.brandName   AS brand,
        p.descri      AS description,
        p.inventoryCount AS stock
      FROM products p
      LEFT JOIN brand b ON p.brandID = b.brandID
      WHERE p.productName LIKE %s
         OR p.descri      LIKE %s
         OR b.brandName   LIKE %s
    """
    # 排序映射
    sort_sql = {
      "sales_desc": "ORDER BY p.sales DESC",
      "price_asc" : "ORDER BY p.price ASC",
      "price_desc": "ORDER BY p.price DESC",
      "sales_asc":"ORDER BY p.rating ASC"
    }.get(sort, "ORDER BY p.sales DESC")
    sql = f"{base_sql} {sort_sql} LIMIT 100"

    try:
        term = f"%{keyword}%"
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (term, term, term))
                rows = cur.fetchall()
    except Exception as e:
        raise HTTPException(500, f"数据库查询失败: {e}")

    # 返回 JSON
    return {"list": rows}

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
                  "SELECT id, username, password, is_admin FROM users WHERE username=%s",
                  (req.username,)
                )
                user = cur.fetchone()
        if not user or not check_password_hash(user["password"], req.password):
            raise HTTPException(401, "用户名或密码错误")
        # Include is_admin in the returned user object
        return {
            "message": "登录成功", 
            "user": {
                "id": user["id"], 
                "username": user["username"],
                "is_admin": bool(user["is_admin"])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"登录失败: {e}")

class GoogleAuthReq(BaseModel):
    token: str

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

class AdminUserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr
    is_admin: Optional[bool] = False

class AdminUserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    is_admin: Optional[bool]

class EmailRequest(BaseModel):
    email: EmailStr
    subject: str = "来自 Buyzu 的问候"
    body: str

@app.get("/admin", response_class=FileResponse)
async def serve_admin():
    # 静态目录 static 下的 admin.html
    return FileResponse("static/admin.html")

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

# 在reco_api_tt.py的"6. 核心推荐、商品、购物车、邮件接口"区域添加以下路由
@app.post("/api/order-summary")
async def order_summary(request: Request):
    user_id = get_owner_key(request)
    with db_conn() as conn:
        with conn.cursor() as cur:
            # 直接从购物车获取商品
            cur.execute("""
                SELECT p.productID, p.productName, p.price, p.img, c.quantity
                FROM carts c
                JOIN products p ON c.productID = p.productID
                WHERE c.userID = %s
            """, (user_id,))
            items = cur.fetchall()
    
    total = sum(float(item['price']) * item['quantity'] for item in items)
    return {
        "cartItems": [{
            "productID": item['productID'],
            "productName": item['productName'],
            "quantity": item['quantity'],
            "price_each": item['price'],
            "img": item['img'],
            "price_subtotal": round(float(item['price']) * item['quantity'], 2)
        } for item in items],
        "totalAmount": round(total, 2)
    }

class ShippingInfo(BaseModel):
    phone: str
    street_address: str
    city: str
    postal_code: str
    country: str
    shipping_method: str = "Fast Delivery"

class PaymentInfo(BaseModel):
    method: str = "credit_card"
    card_last4: str = "0000"

@app.post("/api/place-order")
async def place_order(request: Request, 
                     shipping_info: ShippingInfo, 
                     payment_info: PaymentInfo):
    user_id = get_owner_key(request)
    order_id = str(uuid.uuid4())
    payment_id = str(uuid.uuid4())

    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                # 开始事务
                conn.begin()

                # 1. 获取购物车商品并验证库存
                cur.execute("""
                    SELECT c.productID, c.quantity, p.price, p.inventoryCount
                    FROM carts c
                    JOIN products p ON c.productID = p.productID
                    WHERE c.userID = %s
                """, (user_id,))
                cart_items = cur.fetchall()
                if not cart_items:
                    raise HTTPException(400, "购物车为空")

                total = 0.0
                for item in cart_items:
                    if item['quantity'] > item['inventoryCount']:
                        raise HTTPException(400, f"商品 {item['productID']} 库存不足")
                    total += float(item['price']) * item['quantity']

                # 2. 插入订单
                cur.execute("""
                    INSERT INTO orders (
                        order_id, userID, total_amount, status, payment_method,
                        shipping_method, phone, street_address, city, postal_code, country
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    order_id, user_id, total, 'pending', 'credit_card',
                    shipping_info.shipping_method,
                    shipping_info.phone,
                    shipping_info.street_address,
                    shipping_info.city,
                    shipping_info.postal_code,
                    shipping_info.country
                ))

                # 3. 插入订单项并更新库存
                for item in cart_items:
                    cur.execute("""
                        INSERT INTO order_items (order_id, productID, quantity, price)
                        VALUES (%s, %s, %s, %s)
                    """, (order_id, item['productID'], item['quantity'], item['price']))
                    # 减少库存
                    cur.execute("""
                        UPDATE products 
                        SET inventoryCount = inventoryCount - %s 
                        WHERE productID = %s
                    """, (item['quantity'], item['productID']))

                # 4. 插入支付记录
                cur.execute("""
                    INSERT INTO payments (
                        payment_id, order_id, amount, status, card_last4, transaction_id
                    ) VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    payment_id, order_id, total, 'succeeded',
                    payment_info.card_last4[-4:],
                    f"TRX-{uuid.uuid4().hex[:8]}"
                ))

                # 5. 清空购物车
                cur.execute("DELETE FROM carts WHERE userID = %s", (user_id,))

                conn.commit()
                return {"success": True, "order_id": order_id}

    except pymysql.Error as e:
        conn.rollback()
        raise HTTPException(500, f"数据库错误: {e}")
    
# ──────────────────────────────────────────────────────────────
# 6. 管理员用户管理接口 (/api/admin/...)
# ──────────────────────────────────────────────────────────────

@app.get("/api/admin/users", dependencies=[Depends(admin_required)])
def get_users(page: int = 1, per_page: int = 10):
    offset = (page - 1) * per_page
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) AS total FROM users")
            total = cur.fetchone()["total"]
            cur.execute("""
                SELECT id,username,email,createdAt,
                       CASE WHEN is_admin=1 THEN TRUE ELSE FALSE END AS is_admin
                  FROM users LIMIT %s OFFSET %s
            """, (per_page, offset))
            users = cur.fetchall()
        return {
            "users": users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page -1)//per_page
        }
    except Exception as e:
        raise HTTPException(500, f"服务器错误: {e}")

@app.get("/api/admin/users/{user_id}", dependencies=[Depends(admin_required)])
def get_user(user_id: int):
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id,username,email,createdAt,
                       CASE WHEN is_admin=1 THEN TRUE ELSE FALSE END AS is_admin
                  FROM users WHERE id=%s
            """, (user_id,))
            u = cur.fetchone()
        if not u:
            raise HTTPException(404, "用户不存在")
        return u
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"服务器错误: {e}")

@app.post("/api/admin/users", status_code=201, dependencies=[Depends(admin_required)])
def create_user(data: AdminUserCreate):
    if not all([data.username, data.password, data.email]):
        raise HTTPException(400, "所有字段都是必填的")
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username=%s", (data.username,))
            if cur.fetchone():
                raise HTTPException(400, "用户名已存在")
            cur.execute("SELECT id FROM users WHERE email=%s", (data.email,))
            if cur.fetchone():
                raise HTTPException(400, "邮箱已注册")
            hashed = generate_password_hash(data.password)
            admin_val = 1 if data.is_admin else 0
            cur.execute("""
                INSERT INTO users(username,password,email,is_admin,createdAt)
                VALUES(%s,%s,%s,%s,%s)
            """, (data.username, hashed, data.email, admin_val, datetime.now()))
            conn.commit()
        return {"message": "用户创建成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"服务器错误: {e}")

@app.put("/api/admin/users/{user_id}", dependencies=[Depends(admin_required)])
def update_user(user_id: int, data: AdminUserUpdate):
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE id=%s", (user_id,))
            if not cur.fetchone():
                raise HTTPException(404, "用户不存在")
            updates, params = [], []
            if data.username is not None:
                cur.execute("SELECT id FROM users WHERE username=%s AND id!=%s",
                            (data.username, user_id))
                if cur.fetchone():
                    raise HTTPException(400, "用户名已存在")
                updates.append("username=%s"); params.append(data.username)
            if data.email is not None:
                cur.execute("SELECT id FROM users WHERE email=%s AND id!=%s",
                            (data.email, user_id))
                if cur.fetchone():
                    raise HTTPException(400, "邮箱已注册")
                updates.append("email=%s"); params.append(data.email)
            if data.password is not None:
                updates.append("password=%s")
                params.append(generate_password_hash(data.password))
            if data.is_admin is not None:
                updates.append("is_admin=%s")
                params.append(1 if data.is_admin else 0)
            if not updates:
                raise HTTPException(400, "没有提供要更新的字段")
            params.append(user_id)
            sql = f"UPDATE users SET {','.join(updates)} WHERE id=%s"
            cur.execute(sql, tuple(params))
            if cur.rowcount<1:
                raise HTTPException(500, "更新失败")
            conn.commit()
        return {"message": "用户更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"服务器错误: {e}")

@app.delete("/api/admin/users/{user_id}", dependencies=[Depends(admin_required)])
def delete_user(user_id: int):
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE id=%s", (user_id,))
            if not cur.fetchone():
                raise HTTPException(404, "用户不存在")
            cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
            if cur.rowcount<1:
                raise HTTPException(500, "删除失败")
            conn.commit()
        return {"message": "用户删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"服务器错误: {e}")

@app.get("/api/admin/search-users", dependencies=[Depends(admin_required)])
def search_users(keyword: str = Query(..., min_length=1)):
    term = f"%{keyword}%"
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT id,username,email,createdAt,
                       CASE WHEN is_admin=1 THEN TRUE ELSE FALSE END AS is_admin
                  FROM users WHERE username LIKE %s OR email LIKE %s
            """, (term, term))
            users = cur.fetchall()
        return {"users": users}
    except Exception as e:
        raise HTTPException(500, f"服务器错误: {e}")


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

@app.get("/searchpage.html")
async def serve_checkout():
    return FileResponse("static/searchpage.html")

@app.get("/checkout.html")
async def serve_checkout():
    return FileResponse("static/checkout.html")