import streamlit as st
import pandas as pd
import os

# Load data
FILE_NAME = "data.csv"
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["Name", "Date", "StartTime", "EndTime", "Phone", "Note"])
    df.to_csv(FILE_NAME, index=False)

df = pd.read_csv(FILE_NAME)

st.title("📋 ระบบจัดคิวลูกค้าแผนไทย")

# ----------------------------
# ✅ Add new customer
# ----------------------------
st.header("➕ เพิ่มลูกค้าใหม่")
with st.form("add_form"):
    name = st.text_input("ชื่อ")
    phone = st.text_input("เบอร์โทร")
    date = st.date_input("วันที่")
    start = st.time_input("เวลาเริ่ม")
    end = st.time_input("เวลาสิ้นสุด")
    note = st.text_area("หมายเหตุ")
    submitted = st.form_submit_button("บันทึกข้อมูล")

    if submitted:
        new_data = {
            "Name": name,
            "Date": date.strftime("%Y-%m-%d"),
            "StartTime": start.strftime("%H:%M"),
            "EndTime": end.strftime("%H:%M"),
            "Phone": phone,
            "Note": note
        }
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_csv(FILE_NAME, index=False)
        st.success("เพิ่มลูกค้าเรียบร้อยแล้ว!")

# ----------------------------
# ❌ Delete customer
# ----------------------------
st.header("🗑️ ลบลูกค้า")
for i, row in df.iterrows():
    st.markdown("---")
    col1, col2 = st.columns([5, 1])
    with col1:
        st.write(f"**{row['Name']}** ({row['Date']} {row['StartTime']} - {row['EndTime']})")
    with col2:
        if st.button("ลบ", key=f"delete_{i}"):
            df = df.drop(i)
            df.to_csv(FILE_NAME, index=False)
            st.success(f"ลบ {row['Name']} แล้ว")
            st.experimental_rerun()
