import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

FILE_NAME = "data.csv"

if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["Name", "Date", "StartTime", "EndTime"])
    df.to_csv(FILE_NAME, index=False)

def save_data():
    name = name_entry.get().strip()
    start = start_entry.get().strip()
    end = end_entry.get().strip()
    date = calendar.get_date()
    date = pd.to_datetime(date).strftime("%Y-%m-%d")

    if not name or not start or not end:
        messagebox.showerror("Error", "Please fill in all fields")
        return

    df = pd.read_csv(FILE_NAME)
    duplicate = df[(df["Name"] == name) & (df["Date"] == date)]
    if not duplicate.empty:
        messagebox.showerror("Duplicate", f"{name} already has an appointment on {date}.")
        return

    new_row = pd.DataFrame([[name, date, start, end]], columns=["Name", "Date", "StartTime", "EndTime"])
    new_row.to_csv(FILE_NAME, mode='a', header=False, index=False)
    messagebox.showinfo("Success", "Appointment saved!")

    name_entry.delete(0, tk.END)
    start_entry.delete(0, tk.END)
    end_entry.delete(0, tk.END)

    load_data(selected_date=date)
    load_upcoming()  # <--- โหลดใหม่ทุกครั้งหลังมีการบันทึก

def load_data(selected_date=None):
    for row in tree.get_children():
        tree.delete(row)
    try:
        df = pd.read_csv(FILE_NAME)
        if selected_date:
            df = df[df["Date"] == selected_date]
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))
        draw_gantt_chart(df, selected_date)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load data:\n{e}")
    load_upcoming()  # <--- โหลดใหม่ทุกครั้งที่เปลี่ยนวัน

def draw_gantt_chart(df, selected_date):
    for widget in chart_frame.winfo_children():
        widget.destroy()
    if df.empty or selected_date is None:
        return

    df = df.copy()
    df["StartTimeFull"] = pd.to_datetime(selected_date + " " + df["StartTime"])
    df["EndTimeFull"] = pd.to_datetime(selected_date + " " + df["EndTime"])
    df = df.sort_values(by="StartTimeFull")

    fig, ax = plt.subplots(figsize=(7, max(3, len(df) * 0.6)))
    colors = plt.cm.Paired.colors

    for i, (_, row) in enumerate(df.iterrows()):
        start = row["StartTimeFull"]
        end = row["EndTimeFull"]
        duration = (end - start).seconds / 60
        start_min = start.hour * 60 + start.minute
        ax.barh(i, duration, left=start_min, color=colors[i % len(colors)], height=0.6, edgecolor='black')
        ax.text(start_min + 2, i, f"{row['Name']} ({start.strftime('%H:%M')}-{end.strftime('%H:%M')})", va='center')

    ax.set_xlim(0, 1440)
    ax.set_xticks(range(0, 1441, 60))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(25)])
    ax.set_yticks([])
    ax.invert_yaxis()  # 🔁 ทำให้เวลาเช้าอยู่ด้านบน
    ax.set_xlabel("Time of Day (minutes)")
    ax.set_title(f"Appointment Schedule for {selected_date}")
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)

def export_to_excel():
    try:
        df = pd.read_csv(FILE_NAME)
        df.to_excel("Appointment_Schedule.xlsx", index=False)
        messagebox.showinfo("Success", "Exported to 'Appointment_Schedule.xlsx'")
    except Exception as e:
        messagebox.showerror("Error", f"Export failed:\n{e}")

def on_calendar_select(event):
    selected = calendar.get_date()
    try:
        selected_date = pd.to_datetime(selected).strftime("%Y-%m-%d")
        load_data(selected_date=selected_date)
    except Exception as e:
        messagebox.showerror("Error", f"Invalid date:\n{e}")

def load_upcoming():
    for row in upcoming_tree.get_children():
        upcoming_tree.delete(row)
    try:
        df = pd.read_csv(FILE_NAME)
        df["StartDatetime"] = pd.to_datetime(df["Date"] + " " + df["StartTime"])
        now = datetime.now()
        df = df[df["StartDatetime"] >= now]
        df = df.sort_values(by="StartDatetime")  # 🔁 เรียงตามวันและเวลา
        for _, row in df.iterrows():
            upcoming_tree.insert("", "end", values=[
                pd.to_datetime(row["Date"]).strftime("%Y-%m-%d"),
                row["Name"],
                row["StartTime"],
                row["EndTime"]
            ])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load upcoming appointments:\n{e}")

# ---------------- GUI ----------------
root = tk.Tk()
root.title("Thai Traditional Massage Queue System")
root.geometry("800x1000")

# Input Form
tk.Label(root, text="Name").pack()
name_entry = tk.Entry(root)
name_entry.pack()

tk.Label(root, text="🗕 Select Date").pack()
calendar = Calendar(root, selectmode="day", date_pattern="yyyy-mm-dd")
calendar.pack(pady=10)
calendar.bind("<<CalendarSelected>>", on_calendar_select)

tk.Label(root, text="Start Time (e.g. 10:00)").pack()
start_entry = tk.Entry(root)
start_entry.pack()

tk.Label(root, text="End Time (e.g. 10:30)").pack()
end_entry = tk.Entry(root)
end_entry.pack()

tk.Button(root, text="Save Appointment", command=save_data).pack(pady=5)
tk.Button(root, text="Export to Excel", command=export_to_excel).pack(pady=5)

# Treeview + Scrollbar (Selected Date)
tree_frame = tk.Frame(root)
tree_frame.pack(pady=10, fill='x')
tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
tree_scroll.pack(side="right", fill="y")
tree = ttk.Treeview(tree_frame, columns=("Name", "Date", "StartTime", "EndTime"), show="headings", yscrollcommand=tree_scroll.set, height=7)
for col in ("Name", "Date", "StartTime", "EndTime"):
    tree.heading(col, text=col)
tree.pack(fill='x')
tree_scroll.config(command=tree.yview)

# Gantt Chart
chart_frame = tk.Frame(root)
chart_frame.pack(fill='both', expand=True)

# Upcoming Appointments + Scrollbar
tk.Label(root, text="🗖 Upcoming Appointments").pack()
upcoming_frame = tk.Frame(root)
upcoming_frame.pack(pady=10, fill='x')
upcoming_scroll = ttk.Scrollbar(upcoming_frame, orient="vertical")
upcoming_scroll.pack(side="right", fill="y")
upcoming_tree = ttk.Treeview(upcoming_frame, columns=("Date", "Name", "StartTime", "EndTime"), show="headings", yscrollcommand=upcoming_scroll.set, height=7)
for col in ("Date", "Name", "StartTime", "EndTime"):
    upcoming_tree.heading(col, text=col)
upcoming_tree.pack(fill='x')
upcoming_scroll.config(command=upcoming_tree.yview)

# Initial load
load_data()
load_upcoming()

root.mainloop()
