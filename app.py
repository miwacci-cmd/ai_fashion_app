import os
import re
import io
import yaml
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
import streamlit_authenticator as stauth
from stability_sdk import client as stability_client
from langchain_openai import ChatOpenAI

# --- 1. 環境設定 ---
load_dotenv()
CONFIG_FILE = "config.yaml"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            data = yaml.load(file, Loader=yaml.SafeLoader)
            if data and 'credentials' in data: return data
    return {'credentials': {'usernames': {}}}

def save_config(config_data):
    with open(CONFIG_FILE, 'w') as file:
        yaml.dump(config_data, file, default_flow_style=False)

if 'auth_status' not in st.session_state: st.session_state['auth_status'] = None
if 'username' not in st.session_state: st.session_state['username'] = None

config = load_config()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
stability_api = stability_client.StabilityInference(
    key=os.getenv("STABILITY_KEY"), 
    engine="stable-diffusion-xl-1024-v1-0"
)

st.set_page_config(page_title="AI Fashion Stylist Pro", layout="wide")

# --- CSS: ヘッダーとボタンのブラッシュアップ ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem; }
    .header-row { display: flex; gap: 10px; margin-bottom: 20px; align-items: stretch; }
    .title-box { background-color: #FFF9C4; border-radius: 15px; padding: 0 25px; display: flex; align-items: center; flex: 3; height: 90px; }
    .login-box { background-color: #FFD54F; border-radius: 15px; display: flex; flex-direction: column; justify-content: center; align-items: center; flex: 1; height: 90px; }
    h1 { font-size: 2rem !important; margin: 0 !important; color: #333; }
    .stButton button { border-radius: 8px; font-weight: bold; border: none; }
    .predict-btn button { height: 3.5em; background-color: #ff4b4b !important; color: white !important; }
    .shop-btn { margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. ヘッダー表示 ---
if st.session_state['auth_status']:
    st.markdown(f"""
        <div class="header-row">
            <div class="title-box"><h1>AI Fashion Stylist Pro</h1></div>
            <div class="login-box"><small>Login ID</small><b>{st.session_state["username"]}</b></div>
        </div>
    """, unsafe_allow_html=True)
    _, h_col_btn = st.columns([3, 1])
    with h_col_btn:
        if st.button("ログアウト", key="logout_btn"):
            st.session_state['auth_status'] = None
            st.rerun()
else:
    st.markdown("""
        <div class="header-row">
            <div class="title-box"><h1>AI Fashion Stylist Pro</h1></div>
            <div class="login-box"><b>未ログイン</b></div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. 認証ロジック ---
if not st.session_state['auth_status']:
    _, m_col, _ = st.columns([1, 1.5, 1])
    with m_col:
        mode = st.radio("メニュー", ["ログイン", "新規アカウント作成"], horizontal=True)
        u_in = st.text_input("ユーザー名")
        p_in = st.text_input("パスワード", type="password")
        if mode == "ログイン":
            if st.button("ログインする", type="primary"):
                usernames = config['credentials']['usernames']
                if u_in in usernames and stauth.Hasher().check_pw(p_in, usernames[u_in]['password']):
                    st.session_state['auth_status'], st.session_state['username'] = True, u_in
                    st.rerun()
                else: st.error("認証失敗")
        else:
            if st.button("アカウントを作成する"):
                if u_in and p_in:
                    config['credentials']['usernames'][u_in] = {'name': u_in, 'password': stauth.Hasher().hash(p_in), 'email': f"{u_in}@ex.com"}
                    save_config(config); st.success("作成完了！")

else:
    # 4. メイン画面
    if "my_closet" not in st.session_state:
        st.session_state.my_closet = ["adidas スタンスミス", "黒のチノパン"]

    col1, col2, col3 = st.columns([1, 1.2, 1.5], gap="large")

    with col1:
        st.write("### 🔍 Style Settings")
        gender = st.radio("性別", ["男性", "女性"], horizontal=True)
        season = st.selectbox("季節", ["春", "夏", "秋", "冬"])
        body = st.selectbox("体型", ["筋肉質", "標準的", "痩せ型", "小柄", "プラスサイズ"])
        scene = st.selectbox("シーン", ["カジュアル", "仕事", "デート", "旅行"])
        budget = st.selectbox("予算感", ["プチプラ", "スタンダード", "ハイブランド"])
        
        st.markdown("---")
        st.write("👟 **手持ちアイテム**")
        for idx, item in enumerate(st.session_state.my_closet):
            c_a, c_b = st.columns([5, 1])
            c_a.markdown(f'<p style="font-size:0.9rem; margin-bottom:-5px;">・{item}</p>', unsafe_allow_html=True)
            if c_b.button("×", key=f"del_{idx}"):
                st.session_state.my_closet.pop(idx); st.rerun()
        
        new_item = st.text_input("", placeholder="アイテムを追加", key="add_box")
        if st.button("追加保存"):
            if new_item: st.session_state.my_closet.append(new_item); st.rerun()
        
        st.markdown('<div class="predict-btn">', unsafe_allow_html=True)
        predict_btn = st.button("コーデを提案する", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    if predict_btn:
        with st.spinner("スタイリストが最高の1枚を考案中..."):
            # プロンプトの重み付け指示を強化
            prompt = f"""
            プロのスタイリストとして提案してください。
            【絶対遵守】性別:{gender}, 体型:{body}, 手持ちアイテム:{st.session_state.my_closet} を完璧に反映すること。特に「黒のチノパン」などの色の指定を無視しないでください。

            1. 日本語で解説（トップス、ボトムス、靴、理由）。
            2. 最後に『英語プロンプト：』を記載。
            画像プロンプトには (Full body portrait of a {body} {gender}:1.5), (wearing exact items from closet:1.4), (cinematic lighting:1.2), ({season} background:1.2) を含めて。
            """
            res = llm.invoke([("user", prompt)]).content
            
            with col2:
                st.write("### 💬 AIの助言")
                st.write(res)
                
                # ショッピングボタンの復活と自動生成
                st.markdown("---")
                st.write("🛒 **このアイテムを探す**")
                def get_url(q): return f"https://www.google.com/search?q={q}+通販"
                
                # 正規表現で提案内容からキーワードを簡易抽出
                items_found = re.findall(r"(?:トップス|ボトムス|靴|アイテム)[：:](.*?)\n", res)
                if not items_found: # 抽出失敗時のフォールバック
                    items_found = [f"{gender} {season} ファッション"]
                
                for item in items_found[:3]:
                    st.link_button(f"🔍 {item.strip()}", get_url(item.strip()))
            
            with col3:
                st.write("### 📸 完成イメージ")
                match = re.search(r"英語プロンプト：(.*)", res, re.S)
                if match:
                    p_out = match.group(1).strip()
                    try:
                        # cfg_scaleを上げてプロンプトへの忠実度を高める
                        answers = stability_api.generate(
                            prompt=f"Masterpiece, high quality, photorealistic, {p_out}",
                            width=1024, height=1024, steps=30, cfg_scale=8.5
                        )
                        for resp in answers:
                            for art in resp.artifacts:
                                if art.type == stability_client.generation.ARTIFACT_IMAGE:
                                    st.image(Image.open(io.BytesIO(art.binary)), use_container_width=True)
                    except: st.error("画像生成エラー（クレジット不足の可能性）")
    else:
        with col2: st.info("条件を選んでボタンを押してください")
        with col3: st.info("ここにイメージが表示されます")

st.markdown("---")
st.caption("© 2026 AI Fashion Stylist Pro")