import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# ---------- Supabase کنیکشن ----------
SUPABASE_KEY = "sb_publishable_Ox_Dj02i1a5QU8GY--QxmAYNhCTuFc"
SUPABASE_URL = "https://fojiefzqep1xbjwmbncw.supabase.co"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"ڈیٹا بیس سے کنیکشن میں مسئلہ: {e}")

st.set_page_config(page_title="فارمیسی سوفٹ ویئر", layout="wide")

# ---------- لاگ اِن ----------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 لاگ اِن - فارمیسی سوفٹ ویئر")
    username = st.text_input("یوزر نیم")
    password = st.text_input("پاس ورڈ", type="password")
    if st.button("لاگ اِن کریں"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("یوزر نیم یا پاس ورڈ غلط ہے")
else:
    # ---------- سائیڈ بار (مینو) ----------
    st.sidebar.title("مینو")
    menu = st.sidebar.radio("صفحہ منتخب کریں:", ["دوائیوں کا اسٹاک", "فروخت کریں", "رپورٹ"])
    
    if st.sidebar.button("لاگ آؤٹ"):
        st.session_state.logged_in = False
        st.rerun()

    # ---------- صفحہ 1: اسٹاک ----------
    if menu == "دوائیوں کا اسٹاک":
        st.header("دوائیوں کا اسٹاک")
        
        with st.form("add_medicine"):
            st.subheader("نئی دوا شامل کریں")
            col1, col2, col3 = st.columns(3)
            name = col1.text_input("نام")
            company = col2.text_input("کمپنی")
            price = col3.number_input("قیمت", min_value=0.0, step=10.0)
            col4, col5 = st.columns(2)
            qty = col4.number_input("مقدار", min_value=0, step=1)
            expiry = col5.text_input("ایکسپائری (YYYY-MM-DD)")
            
            if st.form_submit_button("شامل کریں"):
                if name and price and qty:
                    try:
                        supabase.table('medicines').insert({
                            "name": name,
                            "company": company,
                            "price": price,
                            "quantity": qty,
                            "expiry": expiry
                        }).execute()
                        st.success("دوا شامل ہو گئی!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"خرابی: {e}")
                else:
                    st.warning("نام، قیمت اور مقدار لازمی ہیں")
        
        st.divider()
        st.subheader("موجودہ اسٹاک")
        
        try:
            response = supabase.table('medicines').select('*').execute()
            rows = response.data
        except Exception as e:
            rows = []
            st.error(f"ڈیٹا لوڈ کرنے میں مسئلہ: {e}")
        
        if rows:
            h1, h2, h3, h4, h5, h6 = st.columns([1, 2, 2, 1, 1, 2])
            h1.write("**آئی ڈی**")
            h2.write("**نام**")
            h3.write("**کمپنی**")
            h4.write("**قیمت**")
            h5.write("**مقدار**")
            h6.write("**ایکسپائری**")
            st.divider()
            
            for row in rows:
                col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 1, 1, 2])
                col1.write(row['id'])
                col2.write(row['name'])
                col3.write(row['company'])
                col4.write(row['price'])
                if row['quantity'] < 10:
                    col5.error(row['quantity'])
                else:
                    col5.write(row['quantity'])
                col6.write(row['expiry'])
        else:
            st.info("ابھی کوئی دوا شامل نہیں کی گئی")

    # ---------- صفحہ 2: فروخت ----------
    elif menu == "فروخت کریں":
        st.header("دوا فروخت کریں")
        
        try:
            response = supabase.table('medicines').select('*').gt('quantity', 0).execute()
            medicines = response.data
        except Exception as e:
            medicines = []
            st.error(f"ڈیٹا لوڈ کرنے میں مسئلہ: {e}")
        
        if medicines:
            med_options = {f"{m['name']} (اسٹاک: {m['quantity']})": m for m in medicines}
            selected_med = st.selectbox("دوا منتخب کریں:", list(med_options.keys()))
            sell_qty = st.number_input("کتنے عدد بیچنے ہیں؟", min_value=1, step=1)
            
            med = med_options[selected_med]
            
            if st.button("فروخت کریں"):
                if sell_qty > med['quantity']:
                    st.error(f"اسٹاک صرف {med['quantity']} ہے")
                else:
                    total = sell_qty * med['price']
                    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    try:
                        supabase.table('medicines').update({
                            "quantity": med['quantity'] - sell_qty
                        }).eq("id", med['id']).execute()
                        
                        supabase.table('sales').insert({
                            "medicine_name": med['name'],
                            "qty": sell_qty,
                            "total": total,
                            "date": date_now
                        }).execute()
                        
                        st.success(f"✅ فروخت مکمل! کل رقم: {total} روپے")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"فروخت میں خرابی: {e}")
        else:
            st.warning("اسٹاک خالی ہے یا کوئی دوا دستیاب نہیں")

    # ---------- صفحہ 3: رپورٹ ----------
    elif menu == "رپورٹ":
        st.header("فروخت کی رپورٹ")
        
        try:
            response = supabase.table('sales').select('*').order('id', desc=True).execute()
            rows = response.data
        except Exception as e:
            rows = []
            st.error(f"رپورٹ لوڈ کرنے میں مسئلہ: {e}")
        
        if rows:
            sales_data = []
            total_sales = 0
            for row in rows:
                sales_data.append({
                    "آئی ڈی": row['id'],
                    "دوا": row['medicine_name'],
                    "مقدار": row['qty'],
                    "رقم": row['total'],
                    "تاریخ": row['date']
                })
                total_sales += row['total']
            
            st.table(sales_data)
            st.metric("کل فروخت کی رقم", f"{total_sales} روپے")
        else:
            st.info("ابھی کوئی فروخت نہیں ہوئی")
