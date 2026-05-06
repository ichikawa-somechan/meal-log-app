import sys
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import google.generativeai as genai
import os
import csv
import re
from datetime import datetime
from PIL import Image
import pandas as pd

# 設定
st.set_page_config(page_title="AI食事管理アプリ", page_icon="🍽️")
st.title("🍽️ 食材個別保存・完全版")

# 1. 撮影者の選択（追加項目）
user_choice = st.sidebar.radio("撮影者を選択してください", ["自分", "妻"])

# APIキーとスプレッドシート接続の設定
API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=API_KEY)
conn = st.connection("gsheets", type=GSheetsConnection)

uploaded_file = st.file_uploader("写真をアップロード", type=["jpg", "png"])

if uploaded_file:
    # use_container_width=True の警告回避のため width='stretch' を推奨
    image = Image.open(uploaded_file)
    st.image(image, width='stretch')
    
    if st.button(f"{user_choice}さんのデータとして解析・保存"):
        try:
            # モデル設定（最新の安定版モデルを指定）
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = "写真を分析し、最後に必ず『食材リスト：とんかつ,白米,味噌汁』のように全食材をカンマ区切りで1行書いてください。"
            
            response = model.generate_content([prompt, image])
            result_text = response.text
            st.write(result_text)
            
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if "食材リスト：" in result_text:
                raw_str = result_text.split("食材リスト：")[-1].strip()
                items = re.split(r'[,、]', raw_str)
                
                # --- 保存データの作成 ---
                new_rows = []
                for item in items:
                    clean_name = item.strip().replace("*", "").replace("。", "")
                    if clean_name:
                        new_rows.append({"日時": now, "摂取した食べ物": clean_name})
                
                if new_rows:
                    # ユーザーに応じたシート（タブ名）を選択
                    target_sheet = "my_log" if user_choice == "自分" else "wife_log"
                    
                    # 既存データの読み込み
                    # Secretsに設定したURLとワークシート名を指定
                    existing_data = conn.read(
                        spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"],
                        worksheet=target_sheet
                    )
                    
                    # データの結合
                    updated_df = pd.concat([existing_data, pd.DataFrame(new_rows)], ignore_index=True)
                    
                    # スプレッドシートの更新
                    conn.update(
                        spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"],
                        worksheet=target_sheet,
                        data=updated_df
                    )
                
                    st.success(f"スプレッドシートの「{target_sheet}」タブに個別に保存しました！")
                    # キャッシュをクリアして最新データを表示可能にする
                    st.cache_data.clear()
                    
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

# --- 履歴表示（スプレッドシートから読み込み） ---
st.markdown("---")
st.subheader(f"{user_choice}さんの履歴 (最新5件)")
try:
    target_sheet = "my_log" if user_choice == "自分" else "wife_log"
    history_df = conn.read(
        spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"],
        worksheet=target_sheet
    )
    if not history_df.empty:
        st.table(history_df.tail(5))
    else:
        st.info("履歴はまだありません。")
except:
    st.info("スプレッドシートの読み込みに失敗しました。シート名が正しいか確認してください。")
