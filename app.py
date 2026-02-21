import os
import json
import requests
import streamlit as st
from dotenv import load_dotenv
import replicate
from langchain_openai import ChatOpenAI

# ==========================================
# 1. ページ設定 (最優先)
# ==========================================
st.set_page_config(page_title="AI Fashion Stylist Pro", layout="wide")

# ==========================================
# 2. 環境設定 & Secrets 読み込み
# ==========================================
load_dotenv(override=True)

# APIキーの取得
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# 楽天IDの設定 (Secretsから読み込み)
RAKUTEN_APP_ID = st.secrets["RAKUTEN_APPLICATION_ID"]
RAKUTEN_AFFILIATE_ID = st.secrets["RAKUTEN_AFFILIATE_ID"]

if REPLICATE_TOKEN:
    rep_client = replicate.Client(api_token=REPLICATE_TOKEN)

USERS_FILE = "users.json"

# ==========================================
# 3. ユーティリティ関数
# ==========================================

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_closet(username):
    path = f"closet_{username}.json"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return []
    return []

def save_closet(username, data):
    path = f"closet_{username}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def search_rakuten_final(rakuten_query):
    """楽天で商品を検索し、アフィリエイトURLを含むデータを返す"""
    if not RAKUTEN_APP_ID: return []
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "affiliateId": RAKUTEN_AFFILIATE_ID,
        "keyword": rakuten_query,
        "format": "json",
        "hits": 3
    }
    try:
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        return res.json().get("Items", [])
    except:
        return []

def display_rakuten_cards(items):
    """取得したアイテムをオシャレな横並びカードで表示する"""
    if not items or len(items) == 0:
        return 

    st.write("---")
    st.write("### 👗 おすすめの買い足しアイテム")
    cols = st.columns(len(items))

    for i, item in enumerate(items):
        info = item['Item']
        with cols[i]:
            with st.container(border=True):
                if info.get('mediumImageUrls'):
                    st.image(info['mediumImageUrls'][0]['imageUrl'], use_container_width=True)
                name = info['itemName'][:35] + "..." if len(info['itemName']) > 35 else info['itemName']
                st.markdown(f"**{name}**")
                st.markdown(f"#### :red[¥{info['itemPrice']:,}]")
                st.link_button("楽天でチェック", info['affiliateUrl'], use_container_width=True)

# ==========================================
# 4. 認証ゲート
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown('<div style="text-align:center; padding:50px 0;"><h1>👗 AI Fashion Stylist Pro</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["ログイン", "新規登録"])
    with tab1:
        u_login = st.text_input("ユーザー名", key="l_u")
        p_login = st.text_input("パスワード", type="password", key="l_p")
        if st.button("ログイン", use_container_width=True, type="primary"):
            users = load_users()
            if u_login in users and users.get(u_login) == p_login:
                st.session_state.authenticated = True
                st.session_state.username = u_login
                st.rerun()
            else: st.error("認証失敗")
    with tab2:
        u_reg = st.text_input("希望ユーザー名", key="r_u")
        p_reg = st.text_input("希望パスワード", type="password", key="r_p")
        if st.button("作成", use_container_width=True):
            users = load_users(); users[u_reg] = p_reg; save_users(users); st.success("完了")
    st.stop()

# ==========================================
# 5. メインアプリケーション
# ==========================================
if "my_closet" not in st.session_state:
    st.session_state.my_closet = load_closet(st.session_state.username)

h1, h2 = st.columns([8, 1.5])
with h1:
    st.markdown(f'<div style="background-color:#FFF9C4; border-radius:15px; padding:10px 20px;"><h1>AI Fashion Stylist Pro <small style="font-size:0.5em;">User: {st.session_state.username}</small></h1></div>', unsafe_allow_html=True)
with h2:
    if st.button("ログアウト", use_container_width=True):
        st.session_state.authenticated = False; st.rerun()

col1, col2, col3 = st.columns([1, 1.3, 1.7], gap="medium")

with col1:
    st.write("### 🔍 Style Settings")
    gender = st.radio("性別", ["男性", "女性"], horizontal=True, index=1)
    season = st.selectbox("季節", ["春", "夏", "秋", "冬"], index=1)
    body = st.selectbox("体型", ["標準的", "痩せ型", "筋肉質", "小柄", "プラスサイズ"], index=0)
    scene = st.selectbox("シーン", ["カジュアル", "デート", "仕事", "旅行"], index=2)

    st.write("👟 **My Closet**")
    for idx, item in enumerate(st.session_state.my_closet):
        ca, cb = st.columns([5, 1])
        ca.write(f"・{item}")
        if cb.button("×", key=f"del_{idx}"):
            st.session_state.my_closet.pop(idx); save_closet(st.session_state.username, st.session_state.my_closet); st.rerun()

    st.text_input("アイテム追加", key="input_field", placeholder="例: PRADAのバッグ")
    if st.button("クローゼットへ登録", use_container_width=True):
        if st.session_state.input_field:
            st.session_state.my_closet.append(st.session_state.input_field); save_closet(st.session_state.username, st.session_state.my_closet); st.rerun()

    predict_btn = st.button("スタイリング実行", type="primary", use_container_width=True)

if predict_btn:
    with st.spinner("クローゼットの逸品を主役にスタイリング中..."):
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, openai_api_key=OPENAI_KEY)
        
        body_kw = {"プラスサイズ": "大きいサイズ", "小柄": "小さいサイズ", "痩せ型": "細身", "筋肉質": "ストレッチ"}.get(body, "")
        gender_kw = "メンズ" if gender == "男性" else "レディース"

        # 核心的なプロンプト
        advice_prompt = f"""
        あなたはプロのパーソナルスタイリストです。{gender}/{body}体型の方へ、{season}の{scene}に合う装いを提案してください。
        
        【現在の手持ちアイテム（最優先で活用してください）】
        {st.session_state.my_closet}

        【スタイリングの鉄則】
        1. 手持ちアイテムに具体的なブランド名（例：PRADA）がある場合、そのアイテムを主役、または重要なアクセントとして必ずコーディネートに組み込んでください。
        2. 手持ちアイテムが{season}や{scene}に合わない場合のみ無視して良いですが、ブランド品はできる限り活かす方法を考えてください。
        3. 全身黒、または全身白は禁止。必ずコントラストをつけること。
        4. 「おすすめ」は、不足している具体的なアイテム名1つ。
        5. 「楽天検索用キーワード」の作成ルール：
           - 衣類（シャツ、ワンピ、パンツ、アウター等）の場合："{gender_kw} {body_kw} {season} [おすすめの具体的名称]"
           - 小物（ハット、バッグ、靴、アクセ等）の場合："{gender_kw} [おすすめ of 具体的名称]"（体型・季節は不要）
        6. 「画像用プロンプト」は、手持ちのブランド品とおすすめアイテムを組み合わせた全身の具体的描写を英語で。

        形式：
        解説：(日本語。どの手持ちをどう活かしたか記述)
        おすすめ：(名詞1つ)
        楽天検索用キーワード：(指示に従った具体的キーワード)
        画像用プロンプト：(A full body photo of a ... wearing ...)
        """
        
        res = llm.invoke([("user", advice_prompt)]).content
        
        try:
            advice = res.split("解説：")[1].split("おすすめ：")[0].strip()
            suggest = res.split("おすすめ：")[1].split("楽天検索用キーワード：")[0].strip()
            rakuten_q = res.split("楽天検索用キーワード：")[1].split("画像用プロンプト：")[0].strip()
            visual_desc_en = res.split("画像用プロンプト：")[1].strip()
        except:
            st.error("生成形式エラー。もう一度実行してください。")
            st.stop()

        with col2:
            st.markdown('<h3 style="white-space: nowrap; font-size: 1.25rem;">💬 スタイリストの助言</h3>', unsafe_allow_html=True)
            st.write(advice)
            
            # 楽天検索と表示
            items = search_rakuten_final(rakuten_q)
            if items:
                display_rakuten_cards(items)
            else:
                st.write(f"🛒 **買い足し提案: {suggest}**")
                st.link_button("楽天で手動検索", f"https://search.rakuten.co.jp/search/mall/{rakuten_q}/", use_container_width=True)

        with col3:
            st.write("### 📸 完成イメージ (Full Body)")
            body_en_shot = {"プラスサイズ": "plus-size curvy body"}.get(body, f"{body} body")
            gender_en_shot = "woman" if gender == "女性" else "man"
            
            flux_prompt = f"""
            (Full body shot, head-to-toe:2.0). 
            A high-end professional fashion editorial photo. 
            {visual_desc_en}. 
            Model is a {gender_en_shot} with {body_en_shot}.
            Natural daylight, photorealistic, cinematic quality, matte textures.
            """

            try:
                output = rep_client.run("black-forest-labs/flux-1.1-pro", input={"prompt": flux_prompt, "aspect_ratio": "2:3"})
                st.image(str(output), use_container_width=True)
            except Exception as e:
                st.error(f"画像生成エラー: {e}")

st.markdown("---")
st.caption("© 2026 AI Fashion Stylist Pro")
st.markdown('<div style="font-size: 0.75rem; color: gray; border-top: 1px solid #eee; padding-top: 10px;">免責事項：ブランド名は提案用であり、公式な提携を示すものではありません。画像はAIイメージです。</div>', unsafe_allow_html=True)