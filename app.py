import sys
import streamlit as st
import google.generativeai as genai
import os
import csv
import re
from datetime import datetime
from PIL import Image

# ファイルパス
current_dir = os.path.dirname(os.path.abspath(__file__))
COMPONENTS_FILE = os.path.join(current_dir, "meal_components.csv")

# 設定
st.set_page_config(page_title="AI食事管理アプリ", page_icon="🍽️")
st.title("🍽️ 食材個別保存・完全版")

API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)

uploaded_file = st.file_uploader("写真をアップロード", type=["jpg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)
    
    if st.button("解析して個別セルに保存"):
        try:
            # モデル判定
            models = genai.list_models()
            target = 'models/gemini-2.5-flash'
            model = genai.GenerativeModel(target)
            
            prompt = "写真を分析し、最後に必ず『食材リスト：とんかつ,白米,味噌汁』のように全食材をカンマ区切りで1行書いてください。"
            
            response = model.generate_content([prompt, image])
            result_text = response.text
            st.write(result_text)
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if "食材リスト：" in result_text:
                raw_str = result_text.split("食材リスト：")[-1].strip()
                items = re.split(r'[,、]', raw_str)
                
                # Excelで「列」が分かれない問題を解決するため、明示的に delimiter=',' を指定
                file_exists = os.path.exists(COMPONENTS_FILE)
                with open(COMPONENTS_FILE, mode='a', encoding='utf-8-sig', newline='') as f:
                    # ここで強制的に「カンマ」で区切る設定にします
                    writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_MINIMAL)
                    
                    if not file_exists or os.path.getsize(COMPONENTS_FILE) == 0:
                        writer.writerow(["日時", "摂取した食べ物"])
                    
                    for item in items:
                        clean_name = item.strip().replace("*", "").replace("。", "")
                        if clean_name:
                            # 確実に [日時] [食材] の2つのセルに分かれるように書き込み
                            writer.writerow([now, clean_name])
                
                st.success("Excelの各セルに個別に保存しました！")
                st.rerun()
        except Exception as e:
            st.error(f"エラー: {e}")

# 履歴表示
if os.path.exists(COMPONENTS_FILE):
    st.markdown("---")
    with open(COMPONENTS_FILE, mode='r', encoding='utf-8-sig') as f:
        reader = list(csv.reader(f))
        for row in reversed(reader[-15:]):
            st.text(f"セル1: {row[0]} | セル2: {row[1]}")