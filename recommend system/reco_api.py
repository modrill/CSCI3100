# reco_api.py  ── BuyZu 推荐接口 Demo（完整可运行版）
import os, datetime, pymysql
from typing import List, Dict, Any
from contextlib import contextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
app = FastAPI(title="BuyZu Recommendation API", version="0.2.0")

# 跨域（如前端与接口不同源时打开；同源可删）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"]
)

# ──────────────────────────────────────────────────────────────
# 3. 工具函数
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
# 4. 核心接口
# ──────────────────────────────────────────────────────────────
@app.get("/api/home_reco")
def home_reco(request: Request, k: int = 10, refresh: bool = False):
    """
    首页「猜你喜欢」接口
    --------------------
    • 若 header:X-UserID / cookie:SESSIONID 均为空 ⇒ 返回热门榜
    • refresh=true      ⇒ 现算 + 入库 + 返回
    • refresh=false     ⇒ 先查 recommend_home 命中则返回缓存；未命中再现算
    """
    # home_reco 开头
    uid = request.headers.get("X-UserID") or request.cookies.get("SESSIONID")
    algo = "mix"

    # 匿名用户 → 热榜
    if not uid:
        return {"source": "popular", "list": fallback_hot(k)}

    # refresh=true → 即时重算
    if refresh:
        pid_list = recompute_for_user(uid, k)
        save_to_db({uid: pid_list}, algo)
        return {"source": "recomputed", "list": enrich(pid_list)}

    # 读缓存
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

    if rows:  # 命中缓存
        return {"source": "cache", "list": rows}

    # 缓存缺失 -> 即时重算回填
    pid_list = recompute_for_user(uid, k)
    save_to_db({uid: pid_list}, algo)
    return {"source": "cold-start", "list": enrich(pid_list)}

# ──────────────────────────────────────────────────────────────
# 5. 静态资源挂载（放在所有 API 路由之后，避免 404）
# ──────────────────────────────────────────────────────────────
# ① 商品图片：浏览器访问 /images/p1.jpeg
app.mount("/images", StaticFiles(directory="images"), name="images")

# ② 前端 Demo 页面：如有 fe.html 直接丢项目根目录
app.mount("/", StaticFiles(directory=".", html=True), name="root")