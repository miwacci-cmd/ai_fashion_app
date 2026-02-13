import os
import re
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from openai import OpenAI
import os
from stability_sdk import client as stability_client
import importlib.util

# Stability AIのクライアント設定
stability_api = stability_client.StabilityInference(
    key=os.environ["STABILITY_KEY"], # 環境変数または直接指定
    verbose=True,
)
# ------------------------------
# 1. 環境変数読み込み
# ------------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("⚠️ .env に OPENAI_API_KEY を設定してください")
    st.stop()

# ------------------------------
# 2. Streamlitページ設定 & タイトル背景
# ------------------------------
st.set_page_config(page_title="AI Fashion Stylist", layout="wide")

# タイトル背景の画像URL（Unsplashのファッション画像）
header_img_url = "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=2070&auto=format&fit=crop"

st.markdown(f"""
    <div style="
        background-image: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.5)), url('{header_img_url}');
        background-size: cover;
        background-position: center;
        height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border-radius: 15px;
        margin-bottom: 30px;
    ">
        <h1 style="color: white; font-size: 3.2rem; font-weight: bold; text-shadow: 2px 2px 4px #000000; margin: 0;">
            AI Fashion Stylist
        </h1>
        <p style="color: white; font-size: 1.2rem; text-shadow: 1px 1px 2px #000000; margin: 10px 0 0 0;">
            最新のAIがあなたの毎日を彩るコーディネートを提案します
        </p>
    </div>
""", unsafe_allow_html=True)

# ------------------------------
# 3. サイドバー（入力フォーム）
# ------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/wardrobe.png", width=80)
    st.header("🔍 スタイル設定")
    
    gender = st.selectbox("性別", ["男性", "女性"])
    season = st.selectbox("季節", ["春", "夏", "秋", "冬"])
    scene = st.selectbox("シーン", ["デート", "仕事", "カジュアル", "フォーマル"])
    
    # --- 追加：体型選択のプルダウン ---
    body_type = st.selectbox("体型タイプ", [
        "標準的", 
        "痩せ型 (Slim)", 
        "筋肉質 (Muscular)",
        "がっしり (Athletic)", 
        "プラスサイズ (Plus-size)", 
        "小柄 (Petite)"
    ])
    
    # 属性・好み（自由入力）
    style = st.text_input("その他の好み", placeholder="例：モノトーン、着痩せしたい")
    
    st.markdown("---")
    predict_button = st.button("コーデを提案する", use_container_width=True, type="primary")

# ------------------------------
# 4. LLM & API クライアント設定
# ------------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=OPENAI_API_KEY
)

client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------
# 5. メインコンテンツ（処理部分）
# ------------------------------
if predict_button:
    col1, col2 = st.columns([1, 1], gap="large")

    with st.spinner("スタイリストが構成を検討中..."):
        prompt_text = f"""
        あなたは高級ファッション誌のスタイリストです。
        以下の条件に最適な、上質で清潔感のあるコーデを提案し、画像生成用の詳細な英語プロンプトも作成してください。

        【条件】
        性別: {gender}, 体型: {body_type}, 季節: {season}, シーン: {scene}, 好み: {style}
        
        回答は必ず以下の【フォーマット】のみで行ってください。

        【フォーマット】
        トップス：(アイテム名)
        ボトムス：(アイテム名)
        靴：(アイテム名)
        理由：(体型カバーのポイントと、シーンに相応しい理由)
        英語プロンプト：(人物の美しい造形、魅力的な笑顔、高品質な服の質感を強調した詳細な英語)
        """

        try:
            response = llm.invoke([("user", prompt_text)])
            generated_text = response.content

            def extract(label):
                pattern = rf"{label}[：:\s]*(.*?)(?=\n(?:トップス|ボトムス|靴|理由|英語プロンプト)|$)"
                match = re.search(pattern, generated_text, re.DOTALL)
                return match.group(1).strip() if match else "確認中"

            tops = extract("トップス")
            bottoms = extract("ボトムス")
            shoes = extract("靴")
            reason = extract("理由")
            dalle_english_prompt = extract("英語プロンプト")

            with col1:
                st.subheader("💡 AIの提案内容")
                st.markdown(f"""
                <div style="background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #eee; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                    <div style="margin-bottom: 15px;"><strong>👕 トップス:</strong> {tops}</div>
                    <div style="margin-bottom: 15px;"><strong>👖 ボトムス:</strong> {bottoms}</div>
                    <div style="margin-bottom: 15px;"><strong>👟 靴:</strong> {shoes}</div>
                    <div style="background-color: #fcfcfc; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-top: 20px;">
                        <strong>💬 スタイリストの助言</strong><br>{reason}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # アイテム検索ボタン
                st.write("### 🛒 アイテムを探す")
                s_cols = st.columns(3)
                for i, (l, n) in enumerate([("トップス", tops), ("ボトムス", bottoms), ("靴", shoes)]):
                    with s_cols[i]:
                        st.link_button(l, f"https://www.amazon.co.jp/s?k={n}", use_container_width=True)

            with col2:
                st.subheader("📸 イメージ画像 (Stable Diffusion)")
                try:
                    # Stable Diffusion用のネガティブプロンプト（顔が崩れないようにする）
                    negative_prompt = "deformed, distorted, disfigured, scary face, bad anatomy, weird eyes, blurry, low quality, cheap fabric"
                    
                    # 生成リクエスト
                    answers = stability_api.generate(
                        prompt=f"Masterpiece, photorealistic fashion model, {dalle_english_prompt}, beautiful kind face, looking at viewer, detailed skin texture, high quality clothing",
                        seed=992446758, 
                        steps=30, 
                        cfg_scale=7.0,
                        width=512,
                        height=768, # 全身が出やすいように縦長に設定
                        samples=2, # 2枚生成
                    )

                    img_cols = st.columns(2)
                    for i, resp in enumerate(answers):
                        for artifact in resp.artifacts:
                            if artifact.type == stability_client.generation.ARTIFACT_IMAGE:
                                import io
                                from PIL import Image
                                img = Image.open(io.BytesIO(artifact.binary))
                                with img_cols[i]:
                                    st.image(img, caption=f"提案案 {i+1}", use_container_width=True)
                        
                except Exception as img_e:
                    st.error(f"画像生成でエラーが発生しました。APIキーを確認してください。")

        except Exception as e:
            st.error(f"システムエラー: {e}")

# ------------------------------
# 6. フッター
# ------------------------------
st.markdown("---")
st.caption("© 2026 AI Fashion Stylist - Powered by OpenAI")