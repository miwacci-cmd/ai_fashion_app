import os
import re
import io
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from stability_sdk import client as stability_client
from langchain_openai import ChatOpenAI

# --- 1. 環境設定 ---
load_dotenv(override=True)
OPENAI_KEY = os.getenv("OPENAI_API_KEY") 
STABILITY_KEY = os.getenv("STABILITY_KEY")

# --- UI設定 ---
st.set_page_config(page_title="AI Fashion Stylist Pro", layout="wide")
if 'auth_status' not in st.session_state: st.session_state['auth_status'] = True 

if OPENAI_KEY:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, openai_api_key=OPENAI_KEY)
if STABILITY_KEY:
    stability_api = stability_client.StabilityInference(key=STABILITY_KEY, engine="stable-diffusion-xl-1024-v1-0")

# --- ヘッダー ---
st.markdown("""
    <style>
    .title-box { background-color: #FFF9C4; border-radius: 15px; padding: 20px; margin-bottom: 20px; }
    h1 { color: #333; margin: 0; }
    </style>
    <div class="title-box"><h1>AI Fashion Stylist Pro</h1></div>
""", unsafe_allow_html=True)

if st.session_state['auth_status']:
    if "my_closet" not in st.session_state:
        st.session_state.my_closet = ["MONCLERの黒ダウン", "白のチノパン", "ベージュのパンプス"]

    col1, col2, col3 = st.columns([1, 1.2, 1.5], gap="large")

    with col1:
        st.write("### 🔍 Style Settings")
        gender = st.radio("性別", ["男性", "女性"], horizontal=True, index=1)
        season = st.selectbox("季節", ["春", "夏", "秋", "冬"], index=3)
        body = st.selectbox("体型", ["標準的", "痩せ型", "筋肉質", "小柄", "プラスサイズ"], index=0)
        scene = st.selectbox("シーン", ["カジュアル", "デート", "仕事", "旅行"], index=2)
        
        st.write("👟 **手元アイテム**")
        for idx, item in enumerate(st.session_state.my_closet):
            c_a, c_b = st.columns([5, 1])
            c_a.write(f"・{item}")
            if c_b.button("×", key=f"del_{idx}"):
                st.session_state.my_closet.pop(idx); st.rerun()
        
        new_item = st.text_input("アイテム追加")
        if st.button("追加"):
            if new_item: st.session_state.my_closet.append(new_item); st.rerun()
        predict_btn = st.button("コーデを提案する", type="primary", use_container_width=True)

    if predict_btn:
        with st.spinner("黒ダウンと白パンツのコントラストを調整中..."):
            prompt = f"""
            プロのスタイリストとして提案してください。
            
            【厳守ルール】
            1. 上半身は必ず「黒のMONCLERダウンジャケット」です。白ではありません。
            2. 下半身は必ず「白のパンツ」です。
            3. シーンは「仕事」に適した、清潔感のあるオフィスカジュアルにしてください。
            4. 性別は必ず【{gender}】。
            
            属性: {gender}, {body}, {season}, {scene}
            アイテムリスト: {st.session_state.my_closet}
            
            【出力形式】
            解説：(日本語)
            追加アイテム：(1つだけ)
            プロンプト：(英語。Vertical full body shot, (Jet black matte MONCLER jacket:1.6), (Pure white chino trousers:1.5), (Nude beige pumps:1.5))
            """
            
            try:
                res = llm.invoke([("user", prompt)]).content
                advice_part = re.search(r"解説：(.*?)追加アイテム：", res, re.S).group(1).strip()
                new_item_suggest = re.search(r"追加アイテム：(.*?)プロンプト：", res, re.S).group(1).strip()
                p_out = res.split("プロンプト：")[1].strip()

                with col2:
                    st.write("### 💬 スタイリストの助言")
                    st.write(advice_part)
                    st.markdown("---")
                    query = f"{gender}+{body}+{scene}+{new_item_suggest}"
                    st.link_button(f"楽天で {new_item_suggest} を探す", f"https://search.rakuten.co.jp/search/mall/{query}/")

                with col3:
                    st.write("### 📸 完成イメージ")
                    neg_gender = "male, man, boy, facial hair" if gender == "女性" else "female, woman, girl"
                    
                    answers = stability_api.generate(
                        prompt=[
                            stability_client.generation.Prompt(
                                text=f"(Vertical full body shot:1.5), (Adult {gender} fashion model:1.6), (Jet black MONCLER down jacket:1.6), (Pure white trousers:1.6), (Beige high-heeled pumps:1.5), {p_out}", 
                                parameters=stability_client.generation.PromptParameters(weight=1.5)
                            ),
                            stability_client.generation.Prompt(
                                text=f"{neg_gender}, (white jacket:1.6), (white coat:1.6), (all-white:1.5), (sneakers:1.4), cropped legs, blurry", 
                                parameters=stability_client.generation.PromptParameters(weight=-1.5)
                            )
                        ],
                        width=832, height=1216, steps=30, cfg_scale=13.0
                    )
                    for resp in answers:
                        for art in resp.artifacts:
                            if art.type == stability_client.generation.ARTIFACT_IMAGE:
                                st.image(Image.open(io.BytesIO(art.binary)), use_container_width=True)
            except Exception as e:
                st.error(f"エラー: {e}")

st.markdown("---")
st.caption("© 2026 AI Fashion Stylist Pro")