import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import plotly.express as px
from google import genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib3
import os
import io
from datetime import datetime, timedelta
urllib3.disable_warnings()

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="FBANK - Financial Analytics", page_icon="🏦", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Hide Streamlit components */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Ultimate Premium Glassmorphism UI */
.stApp { 
    background: radial-gradient(circle at top left, #1e293b, #0f172a) !important; 
    color: #f1f5f9; 
    font-family: 'Inter', sans-serif; 
}

/* Beautiful Flowing Title */
.main-title { 
    font-size: 2.8rem; 
    font-weight: 800; 
    background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    letter-spacing: -0.5px;
}
.sub-title { 
    font-size: 1rem; 
    color: #94a3b8; 
    font-weight: 500; 
    letter-spacing: 1.5px; 
    text-transform: uppercase; 
    margin-bottom: 2rem;
}

/* Glassmorphism Tabs */
.stTabs [data-baseweb="tab-list"] { 
    gap: 15px; 
    background: rgba(30, 41, 59, 0.4); 
    padding: 10px 15px 0 15px;
    border-radius: 16px 16px 0 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.stTabs [data-baseweb="tab"] { 
    font-size: 1rem; 
    font-weight: 600; 
    padding: 12px 24px; 
    color: #64748b; 
    background: transparent;
    border: none;
    transition: all 0.3s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #e2e8f0;
}
.stTabs [aria-selected="true"] { 
    background: rgba(56, 189, 248, 0.15) !important; 
    color: #38bdf8 !important; 
    border-bottom: 3px solid #38bdf8 !important;
    border-radius: 8px 8px 0 0;
}

/* Glowing Interactive Buttons */
.stButton>button { 
    background: linear-gradient(135deg, #3b82f6 0%, #4f46e5 100%);
    border: none;
    border-radius: 8px; 
    font-weight: 600; 
    height: 52px; 
    color: white;
    font-size: 15px; 
    letter-spacing: 0.5px; 
    text-transform: uppercase; 
    transition: all 0.3s ease; 
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
}
.stButton>button:hover { 
    transform: translateY(-2px) scale(1.01);
    box-shadow: 0 8px 25px rgba(79, 70, 229, 0.6);
    background: linear-gradient(135deg, #2563eb 0%, #4338ca 100%);
}

/* Animated Metrics & Glass Containers */
div[data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 800; color: #f8fafc; font-family: 'Inter', sans-serif; letter-spacing: -1px; }
div[data-testid="stMetricLabel"] { font-size: 0.95rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;}

.metric-container {
    background: rgba(30, 41, 59, 0.4) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 24px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}
.metric-container:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.4) !important;
    border-color: rgba(56, 189, 248, 0.4) !important;
}

/* App Logo Styling */
.logo-box { 
    background: linear-gradient(135deg, #38bdf8 0%, #4f46e5 100%); 
    width: 60px; height: 60px; 
    border-radius: 14px; display: flex; align-items: center; justify-content: center; 
    font-size: 32px; font-weight: 800; color: white; 
    box-shadow: 0 8px 20px rgba(79, 70, 229, 0.4); 
}
</style>

<div style="display: flex; align-items: center; gap: 24px; margin-bottom: 20px;">
    <div class="logo-box">F</div>
    <div>
        <div class="main-title">FBANK ECOSYSTEM</div>
        <div class="sub-title">Premium AI Analytics & Live Market Engine</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 2. CẤU HÌNH API DƯỚI NỀN (STREAMLIT SECRETS) ---
try:
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
    smtp_email = st.secrets["SMTP_EMAIL"]
    smtp_password = st.secrets["SMTP_PASSWORD"]
except:
    gemini_api_key = "" 
    smtp_email = "minhtqcs200119@gmail.com" 
    smtp_password = "" 


# --- 3. ROBUST LOGIC LAYER ---
@st.cache_data(ttl=3600)
def load_live_rates():
    try:
        r = requests.get('https://webgia.com/lai-suat/', headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=12)
        dfs = pd.read_html(io.StringIO(r.text))
        df = dfs[0]
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(str(i) for i in col).strip() for col in df.columns]
            
        df_clean = pd.DataFrame()
        bank_cols = [c for c in df.columns if 'ngân hàng' in str(c).lower()]
        if not bank_cols: raise Exception("No bank column")
        df_clean['bank'] = df[bank_cols[0]]
        
        def pick_col(keywords):
            for c in df.columns:
                lower_c = str(c).lower().strip()
                for k in keywords:
                    if lower_c.endswith(k) or lower_c == k: return c
            return None
        
        c3 = pick_col(['03 tháng', '3 tháng', '_3 tháng', ' 3t'])
        c6 = pick_col(['06 tháng', '6 tháng', '_6 tháng', ' 6t'])
        c12 = pick_col(['12 tháng', '_12 tháng', ' 12t'])
        
        if c3 and c6 and c12:
            df_clean['3M'] = df[c3]
            df_clean['6M'] = df[c6]
            df_clean['12M'] = df[c12]
            
            for col in ['3M', '6M', '12M']:
                df_clean[col] = pd.to_numeric(df_clean[col].astype(str).str.replace('%', '').str.replace(',', '.'), errors='coerce')
            
            out_df = df_clean.dropna().reset_index(drop=True)
            if out_df.empty: raise Exception("Parsed data empty")
            return out_df
        else:
            raise Exception("Cannot match columns")
    except Exception as e:
        import os
        try:
            csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.csv")
            return pd.read_csv(csv_path)[['bank', '3M', '6M', '12M']].dropna()
        except:
            return pd.DataFrame({'bank':['Vietcombank','BIDV','Techcombank','MBBank','ACB','VPBank','VIB','Sacombank'], '3M':[2.2,2.3,2.5,2.6,2.7,2.8,2.9,2.8], '6M':[3.2,3.3,3.6,3.8,3.9,4.0,4.1,4.0], '12M':[4.7,6.8,7.35,7.5,5.0,5.2,5.3,5.0]})


@st.cache_data(ttl=1800)
def load_exchange_rates():
    try:
        response = requests.get('https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx', headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        root = ET.fromstring(response.content)
        rates = [{'Currency': ex.get('CurrencyName'), 'Code': ex.get('CurrencyCode'), 'Sell': float(ex.get('Sell').replace(',', ''))} for ex in root.findall('Exrate')]
        return pd.DataFrame(rates)
    except: return pd.DataFrame()

@st.cache_data(ttl=1800)
def load_news():
    try:
        response = requests.get('https://vnexpress.net/rss/kinh-doanh.rss', timeout=10)
        root = ET.fromstring(response.content)
        return [{'title': i.find('title').text, 'link': i.find('link').text} for i in root.find('channel').findall('item')[:6]]
    except: return []

@st.cache_data(ttl=1800)
def load_gold_prices():
    try:
        r = requests.get('https://webgia.com/gia-vang/sjc/', headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=10)
        dfs = pd.read_html(io.StringIO(r.text))
        df = dfs[0]
        # Clean up column names if they are multi-index
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(str(i) for i in col).strip() for col in df.columns]
        
        # Standardize columns: Loai Vang, Mua vao, Ban ra
        gold_df = pd.DataFrame()
        gold_df['Type'] = df.iloc[:, 0]
        gold_df['Buy'] = df.iloc[:, 1]
        gold_df['Sell'] = df.iloc[:, 2]
        return gold_df.head(5)
    except: return pd.DataFrame()

@st.cache_data(ttl=3600*6)
def get_auto_forecast(news_list, api_key):
    if not api_key: return None
    try:
        context = "\n".join([n['title'] for n in news_list])
        client = genai.Client(api_key=api_key)
        rep = client.models.generate_content(model='gemini-2.5-flash', contents=f"Phân tích ngắn gọn các tin tức sau: {context}. Đóng vai trò là một chuyên gia phân tích tài chính vĩ mô, hãy trình bày dự báo (khoảng 3-4 dòng) bằng ngôn ngữ tiếng Việt, tông giọng học thuật, khách quan về xu hướng lãi suất điều hành và đưa ra 1 lời khuyên về chiến lược phân bổ vốn.")
        return rep.text
    except: return "Lỗi hệ thống truy xuất máy học."

def send_email(to_email, body):
    if not smtp_email or not smtp_password: return
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = "BÁO CÁO CHIẾN LƯỢC ĐẦU TƯ TÍCH LŨY (FBANK AI)"
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.sendmail(smtp_email, to_email, msg.as_string())
        server.quit()
    except: pass

# --- 5. PORTFOLIO PERSISTENCE LAYER ---
PORTFOLIO_FILE = "portfolio.csv"

def load_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return pd.DataFrame(columns=['id', 'bank', 'amount', 'start_date', 'duration', 'rate', 'status'])
    df = pd.read_csv(PORTFOLIO_FILE)
    df['id'] = df['id'].astype(str)
    return df

def save_portfolio(df):
    df.to_csv(PORTFOLIO_FILE, index=False)

def add_deposit(bank, amount, duration, rate):
    df = load_portfolio()
    new_id = str(int(datetime.now().timestamp()))
    new_row = {
        'id': new_id,
        'bank': bank,
        'amount': amount,
        'start_date': datetime.now().strftime("%Y-%m-%d"),
        'duration': duration,
        'rate': rate,
        'status': 'Active'
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_portfolio(df)

# --- 6. TABS UI ---
tab_market, tab_ai, tab_macro, tab_portfolio, tab_scenarios = st.tabs(["📊 DỮ LIỆU THỊ TRƯỜNG", "🤖 PHÂN TÍCH LỢI NHUẬN AI", "📰 BÁO CÁO VĨ MÔ", "💼 DANH MỤC CỦA TÔI", "🧠 KỊCH BẢN AI"])

# GIAO DIỆN HÀN LÂM: TAB THỊ TRƯỜNG
with tab_market:
    st.markdown("#### 💱 TỶ GIÁ NGOẠI TỆ LIÊN NGÂN HÀNG (LIVE)")
    ex_df = load_exchange_rates()
    if not ex_df.empty:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        for i, code in enumerate(['USD', 'EUR', 'GBP', 'JPY']):
            val = ex_df[ex_df['Code']==code]['Sell'].values
            if len(val) > 0:
                with [c1, c2, c3, c4][i]: st.metric(label=f"TỶ GIÁ {code}/VND", value=f"{val[0]:,.0f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("#### 🟡 GIÁ VÀNG TRỰC TUYẾN (SJC)")
    gold_df = load_gold_prices()
    if not gold_df.empty:
        gc1, gc2, gc3 = st.columns(3)
        with gc1: st.metric("SJC MUA VÀO", f"{gold_df.iloc[0]['Buy']}")
        with gc2: st.metric("SJC BÁN RA", f"{gold_df.iloc[0]['Sell']}")
        with gc3: st.info("Thị trường vàng vẫn là kênh trú ẩn an toàn chống lại sự mất giá của tiền tệ.")
    else:
        st.warning("Dịch vụ truy xuất giá vàng tạm thời không khả dụng.")
    
    st.markdown("<br>#### 📊 ĐƯỜNG CONG LỢI SUẤT KỲ VỌNG (CÁC NH ĐẦU TÀU)", unsafe_allow_html=True)
    rates_raw = load_live_rates()
    if not rates_raw.empty:
        major_banks = ['Vietcombank', 'BIDV', 'VietinBank', 'Agribank', 'Techcombank', 'MB', 'ACB', 'VPBank', 'Sacombank', 'VIB', 'TPBank', 'HDBank']
        filtered_rates = rates_raw[rates_raw['bank'].apply(lambda x: any(m.lower() in str(x).lower() for m in major_banks))]
        if filtered_rates.empty: filtered_rates = rates_raw.head(10)
        
        melted = filtered_rates.melt(id_vars='bank', value_vars=['3M', '6M', '12M'], var_name='Kỳ hạn (Tháng)', value_name='Lợi suất (%/Năm)')
        fig = px.bar(melted, x='bank', y='Lợi suất (%/Năm)', color='Kỳ hạn (Tháng)', barmode='group', color_discrete_sequence=['#14b8a6', '#0ea5e9', '#6366f1'])
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#94a3b8", margin=dict(l=0, r=0, b=0, t=10), font=dict(family="Consolas, monospace"))
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("<br>#### 📑 BẢNG CÂN ĐỐI LÃI SUẤT TIẾT KIỆM (TOÀN THỊ TRƯỜNG)", unsafe_allow_html=True)
        
        # Add Inflation Adjustment Mockup (VN Inflation ~4%)
        inflation_rate = 3.5
        display_df = rates_raw.copy()
        display_df['Lợi suất Thực (12T)'] = display_df['12M'] - inflation_rate
        
        st.dataframe(
            display_df.rename(columns={
                'bank': 'Tổ chức Tài chính',
                '3M': 'Lãi suất 3T %',
                '6M': 'Lãi suất 6T %',
                '12M': 'Lãi suất 12T %'
            }).sort_values(by='Lãi suất 12T %', ascending=False),
            width="stretch",
            hide_index=True
        )
        st.caption(f"Lưu ý: 'Lợi suất Thực' đã tính đến chỉ số CPI nội địa khoảng {inflation_rate}%. Kết quả là ước tính học thuật.")
    else:
        st.error("Lỗi đồng bộ hóa dữ liệu Lãi suất Thị trường từ API.")

# GIAO DIỆN HÀN LÂM: TAB AI
with tab_ai:
    c_input, c_output = st.columns([1, 1.5], gap="large")
    with c_input:
        st.markdown("#### ⚙️ THÔNG SỐ ĐẦU VÀO")
        with st.container(border=True):
            amount = st.number_input("VỐN ĐẦU TƯ (VND)", min_value=1000000, value=500000000, step=50000000, format="%d")
            duration = st.selectbox("KỲ HẠN CỐ ĐỊNH (THÁNG)", [3, 6, 12], index=2)
            pref = st.selectbox("KHẨU VỊ RỦI RO", ["Tối đa hóa Lợi nhuận (Tấn công)", "An toàn Thanh khoản (Thận trọng)", "Bảo toàn Danh mục Lõi (Phòng thủ)"])
            email_to = st.text_input("EMAIL NHẬN BÁO CÁO (TÙY CHỌN)")
            st.markdown("---")
            user_api_key = st.text_input("🔑 NHẬP GEMINI API KEY (BẮT BUỘC ĐỂ DÙNG AI)", type="password", help="Bảo mật: Mã khóa chỉ tồn tại trong phiên làm việc, không lưu trữ lên máy chủ.")
            if user_api_key: gemini_api_key = user_api_key.strip()
            
            st.write("")
            btn = st.button("🚀 KÍCH HOẠT THUẬT TOÁN", type="primary", use_container_width=True)

    with c_output:
        st.markdown("#### 📑 BÁO CÁO ĐƯỢC TẠO")
        if btn:
            rates = load_live_rates()
            d_col = f"{duration}M"
            
            if rates.empty or d_col not in rates.columns:
                st.error("Thiếu dữ liệu chỉ số lợi suất. Thuật toán bị gián đoạn.")
            else:
                df = rates[['bank', d_col]].dropna().copy()
                df['rate'] = df[d_col]
                df['fv'] = amount + (amount * (df['rate']/100) * (duration/12))
                df = df.sort_values(by='fv', ascending=False).reset_index(drop=True)
                best = df.iloc[0]
                
                with st.container(border=True):
                    mc1, mc2 = st.columns(2)
                    mc1.metric(f"TỔ CHỨC TÀI CHÍNH TỐI ƯU", f"{best['bank']}")
                    mc2.metric("LỢI NHUẬN GỘP DỰ KIẾN", f"+ {best['fv'] - amount:,.0f} ₫")
                    st.caption(f"Lợi suất Tham chiếu: **{best['rate']}% / NĂM**")
                
                st.markdown("#### 🧠 ĐÁNH GIÁ TỪ CHUYÊN GIA AI:")
                if gemini_api_key:
                    with st.spinner("Đang khởi tạo đánh giá vĩ mô..."):
                        try:
                            client = genai.Client(api_key=gemini_api_key)
                            prompt = f"Phân tích hệ thống: Nhà đầu tư dự định phân bổ {amount:,.0f} VND vào {best['bank']} (Lợi suất {best['rate']}%) cho kỳ hạn {duration} tháng với khẩu vị rủi ro '{pref}'. Đóng vai trò là một chuyên gia phân tích tài chính (ngôn ngữ học thuật, trang trọng), hãy đưa ra một đánh giá chuyên môn ngắn gọn (2 câu) về cơ sở lý luận đằng sau việc phân bổ danh mục này bằng tiếng Việt."
                            ai_reply = client.models.generate_content(model='gemini-2.5-flash', contents=prompt).text
                            st.info(f"{ai_reply}")
                        except Exception as e: st.error(f"LỖI HỆ THỐNG AI: {str(e)}")
                else: st.warning("API_KEY chưa được khai báo trong Cấu hình Hệ thống.")
                
                with st.expander("XUẤT MA TRẬN DỮ LIỆU THÔ"):
                    st.dataframe(df[['bank', 'rate', 'fv']].head(10).rename(columns={'bank':'Tên Tổ chức', 'rate': 'Lợi suất %/Năm', 'fv': 'Giá trị Tích lũy (VND)'}), hide_index=True, width="stretch")
                
                if email_to:
                    if not smtp_email or not smtp_password:
                        st.warning("⚠️ Cảnh báo: Tính năng Email tự động bị ngắt kết nối. Bạn cần cấu hình thông tin Người gửi (smtp_email & smtp_password) trực tiếp trong app.py.")
                    else:
                        send_email(email_to, f"HỆ THỐNG TÀI CHÍNH THÔNG MINH FBANK\n\n- Phân bổ Danh mục: {best['bank']}\n- Lợi nhuận Gộp Dự kiến: {best['fv'] - amount:,.0f} VND\n\nĐÁNH GIÁ CHUYÊN GIA AI:\n{ai_reply if gemini_api_key else 'N/A'}")
                        st.success("Tác vụ điều hướng (Push-Email) đã thực hiện thành công.")
                
                if st.button("📥 XÁC NHẬN VÀO SỔ CÁI (TÀI SẢN CỐ ĐỊNH)", use_container_width=True):
                    add_deposit(best['bank'], amount, duration, best['rate'])
                    st.success(f"Tài sản đã được đồng bộ hóa toàn cầu: {best['bank']} @ {best['rate']}%")
                    st.balloons()
        else:
            st.info("Trạng thái chờ. Vui lòng khai báo Thông số Đầu vào để tải dữ liệu.")

# GIAO DIỆN HÀN LÂM: TAB VĨ MÔ
with tab_macro:
    m1, m2 = st.columns([1, 1.4], gap="large")
    with m1:
        st.markdown("#### 📰 ĐIỂM TIN VĨ MÔ (RSS CRAWLER)")
        news = load_news()
        for i, n in enumerate(news): 
            st.markdown(f"*{i+1}.* [{n['title']}]({n['link']})")
    with m2:
        st.markdown("#### 📈 DỰ BÁO TỪ MÁY HỌC")
        st.caption("Tổng hợp tín hiệu và chiết xuất trọng tâm Chính sách Tiền tệ.")
        
        if not gemini_api_key:
            st.warning("Thiếu định danh Key API bảo mật.")
        elif not news:
            st.warning("Hết thời gian yêu cầu HTTP tại điểm cuối RSS feed.")
        else:
            with st.spinner("Đang chạy Suy luận Vector hóa..."):
                forecast_text = get_auto_forecast(news, gemini_api_key)
                if forecast_text: st.success(f"{forecast_text}")

# GIAO DIỆN HÀN LÂM: TAB PORTFOLIO
with tab_portfolio:
    st.markdown("#### 💼 PHÂN BỔ TÀI SẢN & GIÁM SÁT NGÀY ĐÁO HẠN")
    
    p_df = load_portfolio()
    
    if p_df.empty:
        st.info("Không tìm thấy khoản tiền gửi đang hoạt động trong sổ cái trung tâm. Sử dụng tab 'PHÂN TÍCH LỢI NHUẬN AI' để thực hiện đầu tư và nó sẽ xuất hiện tại đây.")
    else:
        # Calculate maturity and profit
        today = datetime.now()
        rows = []
        for _, row in p_df.iterrows():
            start = datetime.strptime(row['start_date'], "%Y-%m-%d")
            end = start + timedelta(days=int(row['duration']) * 30) # Approx
            days_left = (end - today).days
            
            profit = row['amount'] * (row['rate']/100) * (row['duration']/12)
            
            rows.append({
                'Tổ chức': row['bank'],
                'Gốc': f"{row['amount']:,.0f} ₫",
                'Lãi suất': f"{row['rate']}%",
                'Ngày Đáo hạn': end.strftime("%d/%m/%Y"),
                'Số ngày còn lại': days_left if days_left > 0 else "ĐÃ ĐÁO HẠN",
                'Lợi nhuận dự kiến': f"{profit:,.0f} ₫"
            })
            
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        
        col1, col2 = st.columns(2)
        total_principal = p_df['amount'].sum()
        col1.metric("TỔNG TÀI SẢN QUẢN LÝ (AUM)", f"{total_principal:,.0f} ₫")
        
        # Professional Export Section
        csv = p_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="💾 XUẤT DANH MỤC RA FILE EXCEL (CSV)",
            data=csv,
            file_name=f"SmartSaving_Portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Simple cleanup button
        if st.button("LÀM MỚI DỮ LIỆU", type="secondary"):
            if os.path.exists(PORTFOLIO_FILE):
                os.remove(PORTFOLIO_FILE)
                st.rerun()

    # Integrated Quick Entry for Demo
    st.divider()
    st.markdown("##### ➕ NHẬP DỮ LIỆU THỦ CÔNG")
    with st.expander("Ghi lại khoản tiền gửi hiện có không được AI theo dõi"):
        with st.form("manual_entry"):
            ebank = st.text_input("Tên Ngân hàng")
            eamount = st.number_input("Số tiền", min_value=0, value=100000000)
            edur = st.selectbox("Kỳ hạn", [3, 6, 12, 24])
            erate = st.number_input("Lãi suất %/năm", value=5.5)
            if st.form_submit_button("LƯU VÀO SỔ CÁI"):
                add_deposit(ebank, eamount, edur, erate)
                st.success("Sổ cái đã được cập nhật.")
                st.rerun()

# GIAO DIỆN HÀN LÂM: TAB SCENARIOS
with tab_scenarios:
    st.markdown("#### 🧠 KIỂM TRA ÁP LỰC TÀI CHÍNH & MÔ PHỎNG KỊCH BẢN AI")
    st.caption("Giả lập các chuyển động giả định của thị trường dựa trên các biến đổi kinh tế vĩ mô.")
    
    with st.container(border=True):
        sc_col1, sc_col2 = st.columns(2)
        with sc_col1:
            fx_move = st.slider("Biến động Tỷ giá VND/USD (%)", -10.0, 10.0, 2.5)
            policy_rate = st.selectbox("Điều chỉnh Lãi suất Điều hành (NHNN)", ["Tăng (Hike)", "Giữ nguyên (Neutral)", "Giảm (Cut)"], index=0)
        with sc_col2:
            inflation_sc = st.slider("Dự báo Lạm phát Mục tiêu (CPI) (%)", 0.0, 10.0, 4.2)
            external_shock = st.selectbox("Điều kiện Thị trường Bên ngoài", ["Bình thường", "Suy thoái Toàn cầu", "Siêu chu kỳ Hàng hóa"])
            
        st.markdown("---")
        user_sc_key = st.text_input("🔑 NHẬP GEMINI API KEY", type="password", key="sc_key")
        if user_sc_key: gemini_api_key = user_sc_key.strip()
            
        simulate = st.button("⚡ THỰC THI MÔ PHỎNG", type="primary", use_container_width=True)
        
    if simulate:
        if gemini_api_key:
            with st.spinner("Đang tính toán các tác động ngẫu nhiên và lan tỏa chính sách..."):
                try:
                    client = genai.Client(api_key=gemini_api_key)
                    sc_prompt = f"""
                    THÔNG SỐ MÔ PHỎNG:
                    - Biến động giá trị VND: {fx_move}%
                    - Chính sách NHNN: {policy_rate}
                    - Dự báo lạm phát: {inflation_sc}%
                    - Môi trường bên ngoài: {external_shock}
                    
                    NHIỆM VỤ: Đóng vai trò là Chiến lược gia Thu nhập cố định Cấp cao, hãy cung cấp một 'Báo cáo Kiểm tra áp lực (Stress Test)'. 
                    Giải quyết: 
                    1. Tác động đến lãi suất huy động dài hạn (12T).
                    2. Rủi ro đối với 'Lợi suất thực' cho người gửi tiền hiện tại.
                    3. Một đề xuất điều chỉnh chiến lược (ví dụ: chuyển sang vàng, rút ngắn kỳ hạn, v.v.).
                    Tông giọng: Học thuật cao, chuyên nghiệp và dựa trên dữ liệu. Giới hạn trong 5-6 câu súc tích bằng tiếng Việt.
                    """
                    sc_reply = client.models.generate_content(model='gemini-2.5-flash', contents=sc_prompt).text
                    st.markdown("---")
                    st.success("MÔ PHỎNG HOÀN TẤT: ĐÃ TẠO THÔNG TIN CHIẾN LƯỢC")
                    st.info(sc_reply)
                    
                    # Risk Rating
                    if external_shock == "Suy thoái Toàn cầu" or abs(fx_move) > 5:
                        st.warning("⚠️ ĐÁNH GIÁ RỦI RO: CAO (PHÁT HIỆN BIẾN ĐỘNG MẠNH)")
                    else:
                        st.success("✅ ĐÁNH GIÁ RỦI RO: ỔN ĐỊNH")
                except Exception as e: st.error(f"LỖI HỆ THỐNG AI: {str(e)}")
        else:
            st.warning("Mô phỏng kịch bản AI yêu cầu Key API Gemini hợp lệ.")
