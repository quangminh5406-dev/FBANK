import pandas as pd
import requests

def clean_pct(val):
    try: return float(str(val).replace('%', ''))
    except: return None

def load_live_rates():
    try:
        r = requests.get('https://webgia.com/lai-suat/', headers={'User-Agent': 'Mozilla/5.0'})
        df = pd.read_html(r.text)[0]
        print("Raw columns:", df.columns.tolist())
        
        # Xử lý MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = ['_'.join(str(i) for i in col).strip() for col in df.columns]
        
        print("After flatten:", df.columns.tolist())
            
        col_mapping = {}
        for c in df.columns:
            c_str = str(c).lower()
            if 'ngân hàng' in c_str: col_mapping[c] = 'bank'
            elif '03 tháng' in c_str or '3 tháng' in c_str or '3t' in c_str: col_mapping[c] = '3M'
            elif '06 tháng' in c_str or '6 tháng' in c_str or '6t' in c_str: col_mapping[c] = '6M'
            elif '12 tháng' in c_str or '12t' in c_str: col_mapping[c] = '12M'
            
        print("Col mapping:", col_mapping)
        if 'bank' in col_mapping.values():
            df = df.rename(columns=col_mapping)
            for col in ['3M', '6M', '12M']:
                if col in df.columns: 
                    # Drop duplicate columns (keep first) in case of Online/Offline duplicates
                    if isinstance(df[col], pd.DataFrame): df[col] = df[col].iloc[:, 0]
                    df[col] = df[col].apply(clean_pct)
            
            df = df.loc[:, ~df.columns.duplicated()]
            return df[['bank', '3M', '6M', '12M']].dropna()
        else:
            print("NO BANK COLUMN FOUND!")
            return pd.DataFrame()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

df_result = load_live_rates()
print("FINAL DF EMPTY?", df_result.empty)
import sys
# Avoid cp1252 error
sys.stdout.reconfigure(encoding='utf-8')
print(df_result.head())
