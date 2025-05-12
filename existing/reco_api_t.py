# reco_api.py

import os
import datetime
import pymysql
import demo                # demo.py 中包含 main()，用于预热推荐

from typing import List, Dict, Any
from contextlib import contextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import smtplib
from email.mime.text import MIMEText
from email.header import Header

from pydantic import BaseModel, EmailStr

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

# 跨域（如前端与接口不同源时打开；同源可删）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ──────────────────────────────────────────────────────────────
# 3. SMTP 配置（已写死，直接使用 Google SMTP）
# ──────────────────────────────────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "buyzuec@gmail.com"
SMTP_PASSWORD = "jxigvyjpmzxpxuwj"  # 你的 Google 应用专用密码
EMAIL_FROM    = "buyzuec@gmail.com"

def _send_email(to_email: str, subject: str, content: str):
    """
    使用 Google SMTP（STARTTLS）发送一封邮件
    """
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
# 4. 工具函数
# ──────────────────────────────────────────────────────────────
def fallback_hot(k: int) -> List[Dict]:
    """无 userKey 时返回销量 TOP k"""
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
    """把推荐结果写入 recommend_home"""
    sql = """REPLACE INTO recommend_home
             (userKey, productID, rankNo, algoTag, score, createdAt)
             VALUES (%s,%s,%s,%s,%s,%s)"""
    now = datetime.datetime.now()
    rows = []
    for uid, pids in rec_dict.items():
        for rank, pid in enumerate(pids, 1):
            rows.append((uid, str(pid), rank, algo, None, now))
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, rows)
    print(f"▶️ save_to_db")

def recompute_for_user(uid: str, topk: int) -> List[int]:
    """
    简化版：临时取销量 TopK。
    实际场景可接入 demo.py 里生成的 item_vec 做 KNN。
    """
    sql = "SELECT productID FROM products ORDER BY sales DESC LIMIT %s"
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (topk,))
            return [row["productID"] for row in cur.fetchall()]

def enrich(pid_list: List[int]) -> List[Dict]:
    """根据 productID 列表补充商品信息并保持顺序"""
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
    print(f"▶️ [demo] serve_home invoked")
    demo.main()
    print(f"✔️ [demo] demo.main() completed")
    return templates.TemplateResponse("homepage.html", {"request": request})

# ──────────────────────────────────────────────────────────────
# 6. 核心接口
# ──────────────────────────────────────────────────────────────
@app.get("/api/home_reco")
def home_reco(request: Request, k: int = 10, refresh: bool = False):
    uid = request.headers.get("X-UserID") or request.cookies.get("SESSIONID")
    algo = "mix"
    if not uid:
        return {"source": "popular", "list": fallback_hot(k)}
    if refresh:
        pid_list = recompute_for_user(uid, k)
        save_to_db({uid: pid_list}, algo)
        return {"source": "recomputed", "list": enrich(pid_list)}
    sql = """
      SELECT r.productID, p.productName, p.price, p.img, b.brandName
      FROM   recommend_home r
      JOIN   products p ON r.productID = p.productID
      LEFT JOIN brand b ON p.brandID = b.brandID
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
    pid_list = recompute_for_user(uid, k)
    save_to_db({uid: pid_list}, algo)
    return {"source": "cold-start", "list": enrich(pid_list)}

@app.get("/api/product")
def product_detail(id: str):
    sql = """
      SELECT productID, productName, price, descri AS description,
             inventoryCount AS stock, img
      FROM products
      WHERE productID = %s
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return {
      "productID":   row["productID"],
      "productName": row["productName"],
      "price":       float(row["price"]),
      "stock":       row["stock"],
      "description": row["description"],
      "images":      [row["img"]],
      "reviews":     []
    }

def get_owner_key(request: Request) -> str:
    uid = request.headers.get("X-UserID") or request.cookies.get("SESSIONID")
    if not uid:
        raise HTTPException(status_code=401, detail="缺少用户标识")
    return uid

@app.post("/api/cart")
async def add_to_cart(request: Request):
    body = await request.json()
    pid  = body.get("id")
    qty  = int(body.get("qty", 1))
    if not pid or qty < 1:
        raise HTTPException(status_code=400, detail="参数不合法")
    owner = get_owner_key(request)
    sql = """
      INSERT INTO carts(sessionID, productID, quantity)
      VALUES (%s, %s, %s)
      ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
    """
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (owner, pid, qty))
        conn.commit()
    return {"success": True}

@app.get("/api/cart")
async def list_cart(request: Request):
    owner = get_owner_key(request)
    sql = """
      SELECT p.productID, p.productName, p.price, p.img, b.brandName, c.quantity
      FROM carts c
      JOIN products p ON c.productID = p.productID
      LEFT JOIN brand b ON p.brandID = b.brandID
      WHERE c.ownerKey = %s
      ORDER BY c.createdAt DESC
    """
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (owner,))
        data = cur.fetchall()
    return {"list": data}

@app.delete("/api/cart")
async def delete_cart_item(request: Request, id: str):
    owner = get_owner_key(request)
    sql = "DELETE FROM carts WHERE ownerKey=%s AND productID=%s"
    with db_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (owner, id))
        conn.commit()
    return {"success": True}

@app.get("/api/hot_products")
def hot_products(k: int = 8):
    sql = """
      SELECT p.productID, p.productName, p.price, p.img, b.brandName 
      FROM   products p
      LEFT JOIN brand b ON p.brandID = b.brandID
      ORDER  BY p.sales DESC
      LIMIT  %s
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (k,))
            return {"list": cur.fetchall()}

# ──────────────────────────────────────────────────────────────
# 7. 真发邮件接口
# ──────────────────────────────────────────────────────────────
class EmailRequest(BaseModel):
    email: EmailStr
    subject: str = "Greetings from Buyzu"
    body: str

@app.post("/api/send_email")
async def api_send_email(req: EmailRequest):
    try:
        _send_email(req.email, req.subject, req.body)
        return {"success": True, "message": f"An email has been sent to {req.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")

# ──────────────────────────────────────────────────────────────
# 8. 直接订阅并发欢迎邮件（无需建表）
# ──────────────────────────────────────────────────────────────
class SubscribeRequest(BaseModel):
    email: EmailStr

@app.post("/api/subscribe")
async def api_subscribe(req: SubscribeRequest):
    """
    A welcome email is sent directly after the user clicks Subscribe
    """
    try:
        _send_email(
            req.email,
            "Thank you for subscribing to Buyzu",
            "Welcome to the Buyzu mailing list! You will be the first to receive the latest trends and offers."
        )
        return {"success": True, "message": f"A welcome email has been sent to {req.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send welcome email: {e}")

# ──────────────────────────────────────────────────────────────
# 9. 静态资源挂载（放在所有 API 路由之后，避免 404）
# ──────────────────────────────────────────────────────────────
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/product.html")
async def serve_product(request: Request):
    return FileResponse("static/product.html")

@app.get("/cart.html")
async def serve_cart(request: Request):
    return FileResponse("static/cart.html")

@app.get("/checkout.html")
async def serve_cart(request: Request):
    return FileResponse("static/checkout.html")