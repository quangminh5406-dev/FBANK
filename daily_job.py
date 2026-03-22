import pandas as pd
import requests
import xml.etree.ElementTree as ET
from google import genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib3
import sys

# Disable SSL Warnings
urllib3.disable_warnings()

from app import load_live_rates, get_auto_forecast, load_news, gemini_api_key, smtp_email, smtp_password

def run_daily_job():
    print("--- INITIATING AUTOMATED CRAWLER TASK ---")
    if not smtp_email or not smtp_password:
        print("ERROR: smtp_email and smtp_password are not configured in app.py.")
        return
        
    rates = load_live_rates()
    news = load_news()
    ai_macro = get_auto_forecast(news, gemini_api_key) if gemini_api_key else "AI module inactive."
    
    # Standard assumption parameters
    amount = 500000000
    duration = 12
    d_col = f"{duration}M"
    
    if rates.empty or d_col not in rates.columns:
        print("CRAWL ERROR: Interest rate index table is currently empty.")
        return
        
    df = rates[['bank', d_col]].dropna().copy()
    df['rate'] = df[d_col]
    df['fv'] = amount + (amount * (df['rate']/100) * (duration/12))
    df = df.sort_values(by='fv', ascending=False).reset_index(drop=True)
    best = df.iloc[0]
    
    target_email = smtp_email 
    
    body = f"""HỆ THỐNG TÀI CHÍNH THÔNG MINH FBANK - BÁO CÁO ĐÁNH GIÁ BUỔI SÁNG

[1] TỐI ƯU HÓA DANH MỤC TIỀN GỬI (Giả định: {amount:,.0f} VND - Kỳ hạn {duration} tháng):
-> Tổ chức đề xuất: {best['bank']}
-> Lợi suất niêm yết: {best['rate']}% / Năm
-> Lợi nhuận gộp dự kiến: + {best['fv'] - amount:,.0f} VND

[2] ĐÁNH GIÁ KINH TẾ VĨ MÔ TỪ CHUYÊN GIA AI:
{ai_macro}

-------------
*Báo cáo được tạo tự động (Hệ thống tạo)*
"""

    print("Routing assessment report to:", target_email)
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = target_email
        msg['Subject'] = "[FBANK] BÁO CÁO THỊ TRƯỜNG LÃI SUẤT HÀNG NGÀY"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, target_email, msg.as_string())
        server.quit()
        print("✔ SUCCESS! EMAIL DISPATCHED WITH STATUS CODE 200 OK.")
    except Exception as e:
        print("❌ SMTP TRANSMISSION ERROR:", e)

if __name__ == "__main__":
    run_daily_job()
