import streamlit as st
import sqlite3
from datetime import datetime

# ---------- ڈیٹا بیس ----------
def init_db():
    conn = sqlite3.connect("pharmacy.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        company TEXT,
        price REAL,
        quantity INTEGER,
        expiry TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_name TEXT,
        qty INTEGER,
        total REAL,
        date TEXT
    )""")
    conn.commit()
    conn.close()

init_db()

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
                    conn = sqlite3.connect("pharmacy.db")
                    c = conn.cursor()
                    c.execute("INSERT INTO medicines (name, company, price, quantity, expiry) VALUES (?,?,?,?,?)",
                              (name, company, price, qty, expiry))
                    conn.commit()
                    conn.close()
                    st.success("دوا شامل ہو گئی!")
                    st.rerun()
                else:
                    st.warning("نام، قیمت اور مقدار لازمی ہیں")
        
        st.divider()
        st.subheader("موجودہ اسٹاک")
        
        conn = sqlite3.connect("pharmacy.db")
        c = conn.cursor()
        c.execute("SELECT * FROM medicines")
        rows = c.fetchall()
        conn.close()
        
        if rows:
            # ہیڈر
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
                col1.write(row[0])
                col2.write(row[1])
                col3.write(row[2])
                col4.write(row[3])
                # کم اسٹاک پر سرخ وارننگ
                if row[4] < 10:
                    col5.error(row[4])
                else:
                    col5.write(row[4])
                col6.write(row[5])
        else:
            st.info("ابھی کوئی دوا شامل نہیں کی گئی")

    # ---------- صفحہ 2: فروخت ----------
    elif menu == "فروخت کریں":
        st.header("دوا فروخت کریں")
        
        conn = sqlite3.connect("pharmacy.db")
        c = conn.cursor()
        c.execute("SELECT id, name, price, quantity FROM medicines WHERE quantity > 0")
        medicines = c.fetchall()
        conn.close()
        
        if medicines:
            med_options = {f"{m[1]} (اسٹاک: {m[3]})": m for m in medicines}
            selected_med = st.selectbox("دوا منتخب کریں:", list(med_options.keys()))
            sell_qty = st.number_input("کتنے عدد بیچنے ہیں؟", min_value=1, step=1)
            
            med = med_options[selected_med]
            
            if st.button("فروخت کریں"):
                if sell_qty > med[3]:
                    st.error(f"اسٹاک صرف {med[3]} ہے")
                else:
                    total = sell_qty * med[2]
                    date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    conn = sqlite3.connect("pharmacy.db")
                    c = conn.cursor()
                    c.execute("UPDATE medicines SET quantity=? WHERE id=?", (med[3] - sell_qty, med[0]))
                    c.execute("INSERT INTO sales (medicine_name, qty, total, date) VALUES (?,?,?,?)",
                              (med[1], sell_qty, total, date_now))
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ فروخت مکمل! کل رقم: {total} روپے")
                    st.balloons()
        else:
            st.warning("اسٹاک خالی ہے یا کوئی دوا دستیاب نہیں")

    # ---------- صفحہ 3: رپورٹ ----------
    elif menu == "رپورٹ":
        st.header("فروخت کی رپورٹ")
        
        conn = sqlite3.connect("pharmacy.db")
        c = conn.cursor()
        c.execute("SELECT * FROM sales ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        
        if rows:
            st.table(rows)
            total_sales = sum(row[3] for row in rows)
            st.metric("کل فروخت کی رقم", f"{total_sales} روپے")
        else:
            st.info("ابھی کوئی فروخت نہیں ہوئی")