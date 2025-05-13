#!/usr/bin/env python
# coding: utf-8
# demo_reco_mix.py
# ============================================================
# 0. 通用 import
# ============================================================
import os, random, time, warnings, math
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from mysql.connector import connect
import logging
logging.basicConfig(level=logging.INFO)
# ============================================================
# 1. 数据库配置
# ============================================================
DB_CONFIG = {
    "host": "localhost",
    "port": 3307,
    "user": "root",
    "password": "",
    "database": "buyzu",
    "charset": "utf8mb4"
}

# ============================================================
# 2. 业务参数
# ============================================================
VEC_NPY   = "item_vec.npy"
REC_XLSX  = "rec_results.xlsx"

MODEL_NAME = "all-roberta-large-v1"

TEXT_DIM   = 256
PRICE_DIM  = 154
BRAND_DIM  = 102

PRICE_ENCODER = "rbf"
RBF_GAMMA     = 50.0

TARGET_DIM = 512
TOPK       = 8
KNN        = 50

BL_RATIO   = 0.8

# SASRec参数
MAXLEN = 50
HIDDEN = 64
N_HEAD = 2
N_BLOCK = 2
BATCH   = 128
EPOCH   = 10
LR      = 1e-3
DEVICE  = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"

# ============================================================
# 3. 数据库读取函数
# ============================================================
def fetch_sql(query):
    conn = connect(**DB_CONFIG)
    df = pd.read_sql(query, conn)
    conn.close()

    # 去掉尾部空格并全部转小写列名
    if "productID" in df.columns:
        df["productID"] = (
            df["productID"].astype(str)
                        .str.strip()
                        .astype(int)
        )
    return df

# ============================================================
# 3.1 保存推荐结果到数据库
# ============================================================
def save_to_db(rec_dict, algo="mix"):
    """
    rec_dict = {userKey: [pid1, pid2, ...]}
    """
    import pymysql, datetime
    conn = pymysql.connect(**DB_CONFIG, autocommit=True)
    with conn.cursor() as cur:
        sql = """
        REPLACE INTO recommend_home(userID, productID, rankNo, algoTag, score, createdAt)
        VALUES (%s,%s,%s,%s,%s,%s)
        """
        now = datetime.datetime.now()
        rows = []
        for uid, pids in rec_dict.items():
            for r, pid in enumerate(pids, 1):
                rows.append((uid, str(pid), r, algo, None, now))
        cur.executemany(sql, rows)
    conn.close()
    print(f"✅ 已写入 recommend_home：{len(rows)} 条")

# ============================================================
# 4. 商品向量生成 (适配数据库字段)
# ============================================================
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler, normalize

def safe_dim(want, n_samples, n_feats):
    max_allowed = min(max(1, n_samples - 1), n_feats)
    if want > max_allowed:
        print(f"⚠️  want_dim={want}>{max_allowed}, 用 {max_allowed}")
        want = max_allowed
    return None if want >= n_feats else want

def build_item_vectors():
    if os.path.exists(VEC_NPY):
        print("✅ 向量文件已存在，跳过重建。")
        return

    print("🔸 开始构建商品向量...")
    # 从数据库读取商品数据
    df = fetch_sql("SELECT * FROM products")
    df.rename(columns={"descri": "Description"}, inplace=True)
    
    n = len(df)
    model = SentenceTransformer(MODEL_NAME, device="cpu")

    # 文本特征处理
    text = (df["productName"].astype(str) + ". " +
            df["Description"].fillna("").astype(str)).tolist()
    txt_full = model.encode(text,
                            batch_size=32,
                            show_progress_bar=True,
                            normalize_embeddings=True)
    d = safe_dim(TEXT_DIM, n, txt_full.shape[1])
    txt_vec = PCA(n_components=d, random_state=42).fit_transform(txt_full) if d else txt_full
    txt_vec = normalize(txt_vec.astype("float32"))

    # 价格特征处理
    price = MinMaxScaler().fit_transform(df["price"].values.reshape(-1,1))
    centers = np.linspace(0,1,PRICE_DIM,dtype="float32")
    price_vec = np.exp(-RBF_GAMMA * (price - centers)**2)
    price_vec = normalize(price_vec, norm="l2")

    # 品牌特征处理
    brands = fetch_sql("SELECT brandID, brandName FROM brand")
    brand_map = dict(zip(brands["brandID"], brands["brandName"]))
    df["brand_str"] = df["brandID"].map(brand_map).fillna("Unknown")
    
    brand_full = model.encode(df["brand_str"].tolist(),
                              batch_size=32,
                              normalize_embeddings=True)
    d = safe_dim(BRAND_DIM, n, brand_full.shape[1])
    brand_vec = PCA(n_components=d, random_state=42).fit_transform(brand_full) if d else brand_full
    brand_vec = normalize(brand_vec.astype("float32"))

    # 合并特征
    emb = np.hstack([txt_vec, price_vec, brand_vec]).astype("float32")
    d = safe_dim(TARGET_DIM, *emb.shape)
    if d:
        emb = PCA(n_components=d, random_state=42).fit_transform(emb)
    vec = normalize(emb.astype("float32"), norm="l2")
    np.save(VEC_NPY, vec)
    print(f"✅ 商品向量保存到 {VEC_NPY}")

# ============================================================
# 5. Baseline推荐 (保持原逻辑)
# ============================================================
from sklearn.neighbors import NearestNeighbors
def get_baseline_candidates(vec, meta, hist, id2idx):
    nbrs = NearestNeighbors(metric="cosine", algorithm="brute")
    nbrs.fit(vec)
    idx2pid = meta["productID"].tolist()
    cands_dict = {}
    for uid, seq in hist.items():
        user_vec = normalize(vec[[id2idx[i] for i in seq]].mean(0,keepdims=True))
        _, ind = nbrs.kneighbors(user_vec, n_neighbors=min(KNN, len(vec)))
        cands = [int(idx2pid[i]) for i in ind[0] if idx2pid[i] not in seq][:TOPK]
        cands_dict[uid] = cands
    return cands_dict

# ============================================================
# 6. SASRec模型 (保持原逻辑)
# ============================================================
import torch, torch.nn as nn, torch.optim as optim
from torch.utils.data import DataLoader, Dataset

class SeqDataset(Dataset):
    def __init__(self, hist, id2idx):
        self.data = []
        for seq in hist.values():
            idx = [id2idx[i] for i in seq]
            for t in range(1, len(idx)):
                h = idx[max(0, t - MAXLEN):t]
                self.data.append((h, idx[t]))
    def __len__(self): return len(self.data)
    def __getitem__(self, i):
        h, tgt = self.data[i]
        pad = MAXLEN - len(h)
        return (torch.tensor([0] * pad + h),
                torch.tensor(len(h) - 1 if h else 0),
                torch.tensor(tgt))

class SASRec(nn.Module):
    def __init__(self, emb):
        super().__init__()
        n, dim = emb.shape
        self.static = nn.Embedding.from_pretrained(torch.tensor(emb), freeze=True)
        self.proj   = nn.Linear(dim, HIDDEN, bias=False)
        self.pos    = nn.Embedding(MAXLEN, HIDDEN)
        layer = nn.TransformerEncoderLayer(HIDDEN, N_HEAD, 4*HIDDEN,
                                           batch_first=True)
        self.enc  = nn.TransformerEncoder(layer, N_BLOCK)
        self.norm = nn.LayerNorm(HIDDEN)
    def forward(self, seq, seqlen):
        x = self.proj(self.static(seq)) + self.pos(
            torch.arange(seq.size(1), device=seq.device))
        x = self.norm(x)
        x = self.enc(x)
        o = x[torch.arange(x.size(0)), seqlen]
        logits = o @ self.proj(self.static.weight).T
        return logits

def train_sasrec(vec, hist, id2idx):
    ds = SeqDataset(hist, id2idx)
    if len(ds) == 0:
        print("⚠️ 无用户行为数据，跳过 SASRec 训练")
        return None
    dl = DataLoader(ds, batch_size=BATCH, shuffle=True)
    m  = SASRec(vec).to(DEVICE)
    opt = optim.Adam(m.parameters(), lr=LR)
    cel = nn.CrossEntropyLoss()
    for ep in range(1, EPOCH+1):
        m.train()
        total_loss = 0
        for s, l, t in dl:
            s, l, t = s.to(DEVICE), l.to(DEVICE), t.to(DEVICE)
            logits = m(s, l)
            loss   = cel(logits, t)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += loss.item() * len(t)
        print(f"Epoch {ep}/{EPOCH}  loss={total_loss/len(ds):.4f}")
    return m

def get_sasrec_candidates(model, vec, meta, hist, id2idx):
    if model is None:
        return {u: [] for u in hist}
    idx2pid = meta["productID"].tolist()
    out = {}
    model.eval()
    for uid, seq in hist.items():
        if not seq:
            out[uid] = []
            continue
        idx = [id2idx[i] for i in seq[-MAXLEN:]]
        pad = MAXLEN - len(idx)
        seq_t = torch.tensor([0] * pad + idx, device=DEVICE).unsqueeze(0)
        logit = model(seq_t, torch.tensor([len(idx)-1], device=DEVICE))
        top = torch.topk(logit, TOPK+len(seq)).indices[0].tolist()
        cand = []
        for j in top:
            pid = idx2pid[j]
            if pid not in seq:
                cand.append(pid)
            if len(cand) == TOPK:
                break
        out[uid] = cand
    return out

# ============================================================
# 7. 混合 & 输出
# ============================================================
def mix_and_save(baseline, sasrec, meta, hist, id2idx,
                 topk=TOPK, bl_ratio=BL_RATIO,
                 write_excel=True, write_db=True, algo="mix"):
    idx2pid = meta["productID"].tolist()
    n_bl = int(round(topk * bl_ratio))
    n_sa = topk - n_bl

    hit = tot = 0
    rows = []
    rec_dict = {}

    for uid, seq in hist.items():
        bl = baseline.get(uid, [])
        sa = sasrec.get(uid, [])
        mix = []

        # 1. baseline
        for pid in bl:
            if pid not in mix:
                mix.append(pid)
            if len(mix) == n_bl:
                break

        # 2. sasrec
        for pid in sa:
            if pid not in mix:
                mix.append(pid)
            if len(mix) == topk:
                break

        # 3. 不足 topk，再补
        for pid in bl + sa:
            if pid not in mix:
                mix.append(pid)
            if len(mix) == topk:
                break

        # 4. 评估
        if len(seq) >= 2:
            tot += 1
            hit += int(seq[-1] in mix)

        # 5. 组织一行写 Excel
        row = [uid]
        rec_pid_list = []
        for pid in mix:
            rec_pid_list.append(pid)
            prod = meta[meta["productID"] == pid].iloc[0]
            row.extend([
                pid,
                prod["productName"],
                prod["brand"],
                prod["price"]
            ])
        while len(row) < 1 + topk*4:
            row.extend([""]*4)
        rows.append(row)

        rec_dict[uid] = rec_pid_list

    if write_db:
        save_to_db(rec_dict, algo=algo)
    if write_excel:
        cols = ["userID"] + [
            f"rec{k}_{c}"
            for k in range(1, topk+1)
            for c in ("id","name","brand","price")
        ]
        pd.DataFrame(rows, columns=cols).to_excel(REC_XLSX, index=False)
        print(f"📄 统一结果保存至 {REC_XLSX}")

    if tot:
        print(f"🎯 Mix Hit@{topk}: {hit/tot:.4f}")
    else:
        print("⚠️ 无法评估")

# ============================================================
# 8. 主执行流程封装为 main()
# ============================================================
def main():
    
    # 生成商品向量
    build_item_vectors()

    # ---------- 读商品表 ----------
    print("🔸 加载商品元数据...")
    meta = fetch_sql("SELECT * FROM products")

    # ---------- 读品牌表并映射 ----------
    print("🔸 加载品牌表...")
    brand = fetch_sql("SELECT brandID, brandName FROM brand")
    brand_map = dict(zip(brand["brandID"], brand["brandName"]))
    meta["brand"] = meta["brandID"].map(brand_map).fillna("Unknown")

    # ---------- 读购物车日志 ----------
    print("🔸 加载购物车日志...")
    df = fetch_sql("""
        SELECT 
            CAST(userID AS CHAR) AS uid,  -- 如果希望 uid 为字符串；也可直接使用 userID
            productID,
            createdAt
        FROM carts
        ORDER BY createdAt
    """)
    print(df)

    # ---------- 构建历史 ----------
    id2idx = {pid: i for i, pid in enumerate(meta["productID"])}
    hist = {}
    for r in df.itertuples(index=False):
        hist.setdefault(r.uid, []).append(int(r.productID))
    print("🪵 hist 用户数 =", len(hist))

    # 加载向量
    vec = np.load(VEC_NPY)

    # 基线候选
    print("🔹 生成 Baseline 候选...")
    baseline = get_baseline_candidates(vec, meta, hist, id2idx)

    # SASRec 候选
    print("🔸 训练 & 生成 SASRec 候选...")
    sas_model = train_sasrec(vec, hist, id2idx)
    sasrec    = get_sasrec_candidates(sas_model, vec, meta, hist, id2idx)

    # 混合 & 输出
    print("🔻 混合 & 输出...")
    mix_and_save(baseline, sasrec, meta, hist, id2idx)

if __name__ == "__main__":
    main()