import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
from openpyxl import load_workbook

# ------------------------ Configuration ------------------------
FILE_NAME = "data.csv"
EXCEL_EXPORT = "appointments.xlsx"
PASSWORD = "Akam_morya"
USERNAME = "Akamsila"

# ------------------------ Login Page ------------------------
def login():
    st.markdown("""
        <div style='text-align:center;'>
            <h1 style='color:#2C3E50;'>🔒 Sri Arokaya Login</h1>
        </div>
        """, unsafe_allow_html=True)

    with st.form(key="login_form"):
        username_input = st.text_input("👤 Username")
        password_input = st.text_input("🔑 Password", type="password")
        login_btn = st.form_submit_button("🔓 Login")

        if login_btn:
            if username_input == USERNAME and password_input == PASSWORD:
                st.session_state["logged_in"] = True
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

# ------------------------ Data Functions ------------------------
def load_data():
    if not os.path.exists(FILE_NAME):
        return pd.DataFrame(columns=["Name", "Date", "StartTime", "EndTime", "Phone", "Note"])
    return pd.read_csv(FILE_NAME, dtype={"Phone": str})

def save_appointment(name, date, start, end, phone, note):
    df = load_data()
    new_data = pd.DataFrame([[name, date, start, end, phone, note]],
                            columns=["Name", "Date", "StartTime", "EndTime", "Phone", "Note"])
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)
    st.success("💾 Appointment saved successfully!")
    export_to_excel(df)

def update_appointment(index, name, date, start, end, phone, note):
    df = load_data()
    if index in df.index:
        df.loc[index] = [name, date, start, end, phone, note]
        df.to_csv(FILE_NAME, index=False)
        st.success("✅ แก้ไขเรียบร้อยแล้ว!")
        export_to_excel(df)

def delete_appointment(index):
    df = load_data()
    if index in df.index:
        df = df.drop(index).reset_index(drop=True)
        df.to_csv(FILE_NAME, index=False)
        st.success("🗑️ ลบเรียบร้อยแล้ว!")
        export_to_excel(df)

def export_to_excel(df):
    df["Date"] = pd.to_datetime(df["Date"])
    grouped = df.groupby([df["Date"].dt.year, df["Date"].dt.month])

    with pd.ExcelWriter(EXCEL_EXPORT, engine="openpyxl") as writer:
        for (year, month), group in grouped:
            sheet_name = f"{year}_{month:02d}"
            group = group.drop(columns=["Start", "End"], errors='ignore')
            group.to_excel(writer, sheet_name=sheet_name, index=False)

# ------------------------ Main App ------------------------
def main_app():
    st.markdown("""
        <div style='text-align:center;'>
            <h1 style='color:#2C3E50;'>💆‍♀️ Thai Traditional Massage Queue</h1>
            <p style='color:#7F8C8D;'>Your daily appointment manager</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("---")

    with st.sidebar:
        st.markdown("### ☀️ เมนูหลัก")
        menu = st.radio("เลือกหน้า:", 
                        ["➕ เพิ่มนัดหมาย", 
                         "⏳ นัดหมายที่จะมาถึง", 
                         "📅 นัดหมายทั้งหมด", 
                         "📊 แผนภูมิเวลา"], 
                        key="menu_selection")
        st.markdown("---")
        if st.button("📕 ออกจากระบบ"):
            st.session_state.logged_in = False
            st.rerun()

    df = load_data()

    # เพิ่มนัดหมาย
    if menu == "➕ เพิ่มนัดหมาย":
        with st.form("appointment_form"):
            st.markdown("### 📌 Add New Appointment")
            col1, col2 = st.columns(2)
            name = col1.text_input("👤 Name")
            phone = col2.text_input("📞 Phone Number")
            note = st.text_area("📝 Note")
            col3, col4 = st.columns(2)
            date = col3.date_input("📅 Date", value=datetime.today())
            start_time = col4.time_input("⏰ Start Time", value=datetime.now().time(), key="start_time")
            end_time = col4.time_input("⏱ End Time", value=(datetime.now() + timedelta(hours=1)).time(), key="end_time")

            submitted = st.form_submit_button("➕ Save Appointment")
            if submitted:
                save_appointment(name, date.strftime("%Y-%m-%d"),
                                 start_time.strftime("%H:%M"),
                                 end_time.strftime("%H:%M"),
                                 phone, note)

    # นัดหมายทั้งหมด
    elif menu == "📅 นัดหมายทั้งหมด":
        st.markdown("### 📋 All Appointments")
        search_name = st.text_input("🔍 ค้นหาชื่อลูกค้า", placeholder="ใส่ชื่อลูกค้าที่ต้องการค้นหา...")
        df_filtered = df.copy()
        if search_name:
            df_filtered = df_filtered[df_filtered["Name"].str.contains(search_name, case=False, na=False)]
        df_filtered = df_filtered.sort_values(by=["Date", "StartTime"])

        if not df_filtered.empty:
            if st.button("⬇️ ดาวน์โหลดเป็น Excel"):
                with pd.ExcelWriter(EXCEL_EXPORT, engine="openpyxl", mode="w") as writer:
                    for month, group in df_filtered.groupby(df_filtered["Date"].str[:7]):
                        group.to_excel(writer, sheet_name=month, index=False)
                with open(EXCEL_EXPORT, "rb") as f:
                    st.download_button("📥 Download Excel File", f, file_name=EXCEL_EXPORT)

        rows_per_page = st.selectbox("แสดงจำนวนรายการต่อหน้า", [10, 20, 50], index=0)
        total_rows = len(df_filtered)
        total_pages = (total_rows - 1) // rows_per_page + 1
        page = st.number_input("เลือกหน้า", min_value=1, max_value=total_pages, value=1, step=1)
        start_idx = (page - 1) * rows_per_page
        end_idx = start_idx + rows_per_page
        df_page = df_filtered.iloc[start_idx:end_idx]

        for i, row in df_page.iterrows():
            index = df_filtered.index[start_idx + i]
            with st.expander(f"📌 {row['Date']} {row['StartTime']} - {row['EndTime']} | {row['Name']}"):
                with st.form(f"edit_form_{index}"):
                    col1, col2 = st.columns(2)
                    name = col1.text_input("👤 Name", value=row["Name"])
                    phone = col2.text_input("📞 Phone", value=row["Phone"])
                    note = st.text_area("📝 Note", value=row["Note"])
                    date = st.date_input("📅 Date", value=datetime.strptime(row["Date"], "%Y-%m-%d"))
                    start_time = st.time_input("⏰ Start", value=datetime.strptime(row["StartTime"], "%H:%M").time())
                    end_time = st.time_input("⏱ End", value=datetime.strptime(row["EndTime"], "%H:%M").time())
                    col_btn1, col_btn2 = st.columns(2)
                    if col_btn1.form_submit_button("💾 แก้ไข"):
                        update_appointment(index, name, date.strftime("%Y-%m-%d"),
                                           start_time.strftime("%H:%M"), end_time.strftime("%H:%M"),
                                           phone, note)
                        st.rerun()
                    if col_btn2.form_submit_button("🗑️ ลบ"):
                        delete_appointment(index)
                        st.rerun()

    # นัดหมายที่จะมาถึง
    elif menu == "⏳ นัดหมายที่จะมาถึง":
        st.markdown("### ⏳ นัดหมายที่จะมาถึง")
        if not df.empty:
            df["Start"] = pd.to_datetime(df["Date"] + " " + df["StartTime"])
            df_upcoming = df[df["Start"] >= datetime.now()].sort_values("Start")
            for i, row in df_upcoming.iterrows():
                index = row.name
                with st.expander(f"📌 {row['Date']} {row['StartTime']} - {row['EndTime']} | {row['Name']}"):
                    with st.form(f"upcoming_edit_form_{index}"):
                        col1, col2 = st.columns(2)
                        name = col1.text_input("👤 Name", value=row["Name"])
                        phone = col2.text_input("📞 Phone", value=row["Phone"])
                        note = st.text_area("📝 Note", value=row["Note"])
                        date = st.date_input("📅 Date", value=datetime.strptime(row["Date"], "%Y-%m-%d"))
                        start_time = st.time_input("⏰ Start", value=datetime.strptime(row["StartTime"], "%H:%M").time())
                        end_time = st.time_input("⏱ End", value=datetime.strptime(row["EndTime"], "%H:%M").time())
                        col_btn1, col_btn2 = st.columns(2)
                        if col_btn1.form_submit_button("💾 แก้ไข"):
                            update_appointment(index, name, date.strftime("%Y-%m-%d"),
                                               start_time.strftime("%H:%M"), end_time.strftime("%H:%M"),
                                               phone, note)
                            st.rerun()
                        if col_btn2.form_submit_button("🗑️ ลบ"):
                            delete_appointment(index)
                            st.rerun()
        else:
            st.info("📭 ยังไม่มีนัดหมายถัดไป")

    # แผนภูมิเวลา
    elif menu == "📊 แผนภูมิเวลา":
        st.markdown("### 📊 แผนภูมิการนัดหมายแยกตามวัน")
        if not df.empty:
            df["Start"] = pd.to_datetime(df["Date"] + " " + df["StartTime"])
            df["End"] = pd.to_datetime(df["Date"] + " " + df["EndTime"])
            selected_date = st.date_input("📆 เลือกวันที่ต้องการดูนัดหมาย", value=datetime.today())
            df_filtered = df[df["Start"].dt.date == selected_date]
            if not df_filtered.empty:
                fig = px.timeline(df_filtered, x_start="Start", x_end="End", y="Name", color="Name",
                                  title=f"🕒 นัดหมายประจำวันที่ {selected_date.strftime('%d %B %Y')}", height=500)
                fig.update_layout(xaxis_title="เวลา", yaxis_title="ลูกค้า",
                                  xaxis=dict(type="date", tickformat="%H:%M"), template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"❗ ไม่มีนัดหมายในวันที่ {selected_date.strftime('%d %B %Y')}")
        else:
            st.info("🔍 ไม่มีข้อมูลนัดหมายในระบบ")

# ------------------------ Session Init ------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
else:
    main_app()
