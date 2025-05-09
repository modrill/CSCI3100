# reco_api.py ── 只读 recommend_home 的极简接口
import pymysql, datetime
from typing import Dict, Any, List
from contextlib import contextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ──────────────────────────────
# 1. 数据库配置
# ──────────────────────────────
DB_CONFIG: Dict[str, Any] = dict(
    host="localhost",
    port=3307,           # 按需调整
    user="root",
    password="",
    database="buyzu",
    charset="utf8mb4",
    cursorclass=pymysql.cursors.DictCursor,
)

@contextmanager
def db_conn():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

# ──────────────────────────────
# 2. FastAPI 基础
# ──────────────────────────────
app = FastAPI(title="BuyZu Recommendation API (No-Hot)", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ──────────────────────────────
# 3. 首页推荐接口（仅读表）
# ──────────────────────────────
@app.get("/api/home_reco")
def home_reco(request: Request, k: int = 10):
    """
    读取 recommend_home，按 rankNo 返回前 k 条。
    若缺少 userKey 或查询不到记录 → list 为空。
    """
    uid = request.headers.get("X-UserID") or request.cookies.get("SESSIONID")
    if not uid:                       # 没有任何身份，直接返回空
        return {"source": "no-userkey", "list": []}

    sql = """
      SELECT r.productID, p.productName, p.price, p.img, b.brandName
      FROM   recommend_home r
      JOIN   products p ON r.productID = p.productID
      LEFT JOIN brand  b ON p.brandID  = b.brandID
      WHERE  r.userKey = %s
      ORDER  BY r.rankNo
      LIMIT  %s
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (uid, k))
            rows: List[Dict] = cur.fetchall()
            
    # -------------- 这里是调试输出 -----------------
    print(f"[home_reco] uid={uid!r}, k={k}, rows={rows}")
    # ----------------------------------------------

    return {
        "source": "recommend_home" if rows else "empty",
        "list"  : rows
    }

# ──────────────────────────────
# 4. 静态资源挂载
# ──────────────────────────────
app.mount("/images", StaticFiles(directory="images"), name="images")
app.mount("/",        StaticFiles(directory=".", html=True), name="root")