import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# =============================================================================
# --- 1. Constants and Initial Setup ---
# =============================================================================
FILE_NAME = "data.csv"
APP_TITLE = "Thai Traditional Massage Queue System"

# Color Palette
PRIMARY_COLOR = "#2C3E50"  # Dark Blue/Grey for main elements
ACCENT_COLOR = "#3498DB"   # Bright Blue for highlights/buttons
BACKGROUND_COLOR = "#ECF0F1" # Light Grey for general background
TEXT_COLOR = "#2C3E50"      # Dark text

# Font Definitions - Adjusted for better readability
# You can try 'Tahoma', 'Verdana', 'Sans-serif', or 'Kanit' if available
HEADER_FONT = ("Segoe UI", 18, "bold") # Increased size
SUBHEADER_FONT = ("Segoe UI", 13, "bold") # Increased size
NORMAL_FONT = ("Segoe UI", 10) # Increased size
BUTTON_FONT = ("Segoe UI", 10, "bold") # Increased size

# Ensure the data file exists and has all columns
REQUIRED_COLUMNS = ["Name", "Date", "StartTime", "EndTime", "Phone", "Note"]
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    df.to_csv(FILE_NAME, index=False)
else:
    # Check if existing CSV has new columns, add if missing
    # Explicitly specify dtype for 'Phone' column to be string
    df = pd.read_csv(FILE_NAME, dtype={'Phone': str})
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = '' # Add missing column with empty string as default
    df = df[REQUIRED_COLUMNS] # Ensure column order
    df.to_csv(FILE_NAME, index=False)


# Global variable to store the currently selected date for filtering
current_selected_date = None

# =============================================================================
# --- 2. Core Functions ---
# =============================================================================

def save_data():
    """Saves new appointment data to the CSV file, with validation."""
    name = name_entry.get().strip()
    phone = phone_entry.get().strip()
    note = note_text.get("1.0", tk.END).strip().replace('\n', ' ')

    # Ensure phone number is treated as string, even if empty
    if not phone:
        phone = "" # Store empty string if no input

    try:
        start_hour = int(start_hour_spinbox.get())
        start_minute = int(start_minute_spinbox.get())
        end_hour = int(end_hour_spinbox.get())
        end_minute = int(end_minute_spinbox.get())

        start = f"{start_hour:02d}:{start_minute:02d}"
        end = f"{end_hour:02d}:{end_minute:02d}"
    except ValueError:
        messagebox.showerror("Error", "Please enter valid numbers for hours and minutes.")
        return

    selected_date_str = calendar.get_date()
    try:
        date_obj = datetime.strptime(selected_date_str, "%m/%d/%y")
        date_formatted = date_obj.strftime("%Y-%m-%d")
    except ValueError as e:
        messagebox.showerror("Error", f"Invalid date format from calendar: {selected_date_str}. Please select a date. Error: {e}")
        return

    if not name or not start or not end:
        messagebox.showerror("Error", "Please fill in all fields (Name, Start Time, End Time).")
        return

    try:
        start_dt = datetime.strptime(f"{date_formatted} {start}", "%Y-%m-%d %H:%M")
        end_dt = datetime.strptime(f"{date_formatted} {end}", "%Y-%m-%d %H:%M")
        
        if start_dt >= end_dt:
            messagebox.showerror("Error", "End Time must be after Start Time.")
            return
    except ValueError:
        messagebox.showerror("Error", "An unexpected time format error occurred. Please check your input.")
        return

    # Read CSV, explicitly specifying dtype for 'Phone'
    df = pd.read_csv(FILE_NAME, dtype={'Phone': str})

    duplicate_name_date = df[(df["Name"] == name) & (df["Date"] == date_formatted)]
    if not duplicate_name_date.empty:
        messagebox.showerror("Duplicate", f"{name} already has an appointment on {date_formatted}.")
        return

    df_on_selected_date = df[df["Date"] == date_formatted].copy()
    if not df_on_selected_date.empty:
        df_on_selected_date["StartTimeFull"] = pd.to_datetime(df_on_selected_date["Date"] + " " + df_on_selected_date["StartTime"])
        df_on_selected_date["EndTimeFull"] = pd.to_datetime(df_on_selected_date["Date"] + " " + df_on_selected_date["EndTime"])

        for _, existing_row in df_on_selected_date.iterrows():
            if not (end_dt <= existing_row["StartTimeFull"] or start_dt >= existing_row["EndTimeFull"]):
                messagebox.showerror("Overlap Error", f"The new appointment for {name} ({start}-{end}) overlaps with an existing appointment for {existing_row['Name']} ({existing_row['StartTime']}-{existing_row['EndTime']}).")
                return

    # Add Phone and Note to the new row
    new_row = pd.DataFrame([[name, date_formatted, start, end, phone, note]], 
                           columns=["Name", "Date", "StartTime", "EndTime", "Phone", "Note"])
    new_row.to_csv(FILE_NAME, mode='a', header=False, index=False)
    messagebox.showinfo("Success", "Appointment saved!")

    name_entry.delete(0, tk.END)
    phone_entry.delete(0, tk.END)
    note_text.delete("1.0", tk.END)
    start_hour_spinbox.set(9)
    start_minute_spinbox.set(0)
    end_hour_spinbox.set(10)
    end_minute_spinbox.set(0)

    load_data(selected_date=date_formatted)
    load_upcoming(filter_name=upcoming_filter_entry.get().strip())

def load_data(selected_date=None, filter_name=""):
    """
    Loads appointment data into the main Treeview and draws Gantt chart.
    Can also filter by name.
    """
    global current_selected_date
    current_selected_date = selected_date

    for row in tree.get_children():
        tree.delete(row)
    try:
        # Read CSV, explicitly specifying dtype for 'Phone'
        df = pd.read_csv(FILE_NAME, dtype={'Phone': str})
        # Ensure 'Phone' and 'Note' columns exist when loading
        for col in ["Phone", "Note"]:
            if col not in df.columns:
                df[col] = ''

        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

        df_filtered_by_date = df[df["Date"] == selected_date] if selected_date else df.copy()

        if filter_name:
            df_filtered = df_filtered_by_date[df_filtered_by_date["Name"].str.contains(filter_name, case=False, na=False)]
        else:
            df_filtered = df_filtered_by_date

        for _, row in df_filtered.iterrows():
            tree.insert("", "end", values=list(row[["Name", "Date", "StartTime", "EndTime", "Phone", "Note"]]))

        if selected_date:
            draw_gantt_chart(df_filtered_by_date, selected_date)
        else:
            for widget in chart_frame.winfo_children():
                widget.destroy()
            if hasattr(root, '_gantt_canvas') and root._gantt_canvas:
                root._gantt_canvas.get_tk_widget().pack_forget()
                root._gantt_canvas = None
            tk.Label(chart_frame, text="Select a date from the calendar to view its schedule.",
                     bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=SUBHEADER_FONT).pack(pady=20)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load data: {e}")

    load_upcoming(filter_name=upcoming_filter_entry.get().strip())

def draw_gantt_chart(df_data, selected_date):
    """Draws a Gantt-like chart for appointments of a selected date."""
    for widget in chart_frame.winfo_children():
        widget.destroy()

    if df_data.empty:
        tk.Label(chart_frame, text=f"No appointments for {selected_date}",
                 bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=SUBHEADER_FONT).pack(pady=20)
        return

    df_data = df_data.copy()
    df_data["StartTimeFull"] = pd.to_datetime(selected_date + " " + df_data["StartTime"])
    df_data["EndTimeFull"] = pd.to_datetime(selected_date + " " + df_data["EndTime"])
    df_data = df_data.sort_values(by="StartTimeFull")

    fig = Figure(figsize=(9, max(4, len(df_data) * 0.7)), dpi=100, facecolor=BACKGROUND_COLOR)
    ax = fig.add_subplot(111)

    colors = [plt.cm.tab10(i) for i in range(len(df_data))]

    for i, (_, row) in enumerate(df_data.iterrows()):
        start = row["StartTimeFull"]
        end = row["EndTimeFull"]
        duration_minutes = (end - start).total_seconds() / 60
        start_minute_of_day = start.hour * 60 + start.minute

        ax.barh(i, duration_minutes, left=start_minute_of_day,
                color=colors[i], height=0.6, edgecolor='black', linewidth=0.8)

        text_x_pos = start_minute_of_day + 5
        ax.text(text_x_pos, i, f"{row['Name']} ({start.strftime('%H:%M')}-{end.strftime('%H:%M')})",
                va='center', ha='left', color='black', fontsize=7, weight='bold')

    ax.set_xlim(0, 1440) # Full 24 hours in minutes

    major_ticks = range(0, 1441, 60)
    minor_ticks = range(0, 1441, 30)
    ax.set_xticks(major_ticks)
    ax.set_xticks(minor_ticks, minor=True)

    ax.set_xticklabels([f"{h:02d}:00" for h in range(25)], fontsize=8)

    ax.set_yticks([])
    ax.invert_yaxis()

    ax.set_xlabel("Time of Day", fontsize=8, color=TEXT_COLOR)
    ax.set_title(f"Appointment Schedule for {selected_date}", fontsize=12, color=PRIMARY_COLOR, weight='bold')

    ax.xaxis.grid(True, which='major', linestyle='--', linewidth=0.5, color='gray', alpha=0.7)
    ax.xaxis.grid(True, which='minor', linestyle=':', linewidth=0.3, color='gray', alpha=0.5)
    ax.set_facecolor("lightgray")

    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill='both', expand=True, padx=5, pady=2)

    root._gantt_canvas = canvas

def export_to_excel():
    """Exports all appointment data to an Excel file."""
    try:
        # Read CSV, explicitly specifying dtype for 'Phone'
        df = pd.read_csv(FILE_NAME, dtype={'Phone': str})
        # Ensure 'Phone' and 'Note' columns exist before exporting
        for col in ["Phone", "Note"]:
            if col not in df.columns:
                df[col] = ''
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df.to_excel("Appointment_Schedule.xlsx", index=False)
        messagebox.showinfo("Success", "Exported to 'Appointment_Schedule.xlsx'")
    except Exception as e:
        messagebox.showerror("Export Failed", f"Export failed: {e}")

def on_calendar_select(event=None):
    """Callback when a date is selected on the calendar."""
    try:
        global current_selected_date
        selected_date = datetime.strptime(calendar.get_date(), "%m/%d/%y").strftime("%Y-%m-%d")
        current_selected_date = selected_date
        root.title(f"{APP_TITLE} | Appointments for {selected_date}")
        load_data(selected_date=selected_date, filter_name=filter_entry.get().strip())
    except ValueError as e:
        messagebox.showerror("Error", f"Invalid date format from calendar: {calendar.get_date()}. Please select a date. Error: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred during date selection:\n{e}")

def load_upcoming(filter_name=""):
    """Loads and displays upcoming appointments in a separate Treeview."""
    for row in upcoming_tree.get_children():
        upcoming_tree.delete(row)
    try:
        # Read CSV, explicitly specifying dtype for 'Phone'
        df = pd.read_csv(FILE_NAME, dtype={'Phone': str})
        # Ensure 'Phone' and 'Note' columns exist when loading
        for col in ["Phone", "Note"]:
            if col not in df.columns:
                df[col] = ''
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')

        df["StartDatetime"] = pd.to_datetime(df["Date"] + " " + df["StartTime"])
        df["EndDatetime"] = pd.to_datetime(df["Date"] + " " + df["EndTime"])
        now = datetime.now()

        df = df[df["EndDatetime"] >= now]
        df = df.sort_values(by="StartDatetime")

        if filter_name:
            df = df[df["Name"].str.contains(filter_name, case=False, na=False)]

        for _, row in df.iterrows():
            upcoming_tree.insert("", "end", values=[
                row["Date"],
                row["Name"],
                row["StartTime"],
                row["EndTime"],
                row["Phone"],
                row["Note"]
            ])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load upcoming appointments:\n{e}")

def go_home():
    """Resets the view to show all appointments and the main title."""
    global current_selected_date
    current_selected_date = None
    filter_entry.delete(0, tk.END)
    upcoming_filter_entry.delete(0, tk.END)
    root.title(f"Home | {APP_TITLE}")
    load_data(selected_date=None)
    calendar.selection_clear()

    for widget in chart_frame.winfo_children():
        widget.destroy()
    if hasattr(root, '_gantt_canvas') and root._gantt_canvas:
        root._gantt_canvas.get_tk_widget().pack_forget()
        root._gantt_canvas = None
    tk.Label(chart_frame, text="Select a date from the calendar to view its schedule.",
             bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=SUBHEADER_FONT).pack(pady=20)

def apply_filter(event=None):
    """Applies the name filter to the current selected date's appointments."""
    load_data(selected_date=current_selected_date, filter_name=filter_entry.get().strip())

def apply_upcoming_filter(event=None):
    """Applies the name filter to upcoming appointments."""
    load_upcoming(filter_name=upcoming_filter_entry.get().strip())


# =============================================================================
# --- 3. GUI Setup ---
# =============================================================================

# Main Window Initialization
root = tk.Tk()
root.title(f"Home | {APP_TITLE}")
root.geometry("1000x700")
root.configure(bg=BACKGROUND_COLOR)

# --- Style Configuration for ttk widgets ---
style = ttk.Style()
style.theme_use('clam')

style.configure('TFrame', background=BACKGROUND_COLOR)
style.configure('TLabel', background=BACKGROUND_COLOR, foreground=TEXT_COLOR, font=NORMAL_FONT)
style.configure('TEntry', font=NORMAL_FONT)
style.configure('TSpinbox', font=NORMAL_FONT)

style.configure('TButton', background=ACCENT_COLOR, foreground='white', font=BUTTON_FONT, padding=8, relief='flat') # Increased padding
style.map('TButton', background=[('active', PRIMARY_COLOR)], foreground=[('active', 'white')])

style.configure('Treeview.Heading', font=SUBHEADER_FONT, background=PRIMARY_COLOR, foreground='white', padding=5) # Increased padding
style.configure('Treeview', font=NORMAL_FONT, rowheight=26, background='white', foreground=TEXT_COLOR, fieldbackground='white') # Increased rowheight
style.map('Treeview', background=[('selected', ACCENT_COLOR)])

# --- Header Frame (Title and Home Button) ---
header_frame = tk.Frame(root, bg=PRIMARY_COLOR, padx=10, pady=8)
header_frame.pack(side=tk.TOP, fill=tk.X)

tk.Label(header_frame, text=APP_TITLE, font=HEADER_FONT, fg="white", bg=PRIMARY_COLOR).pack(side=tk.LEFT, padx=8)
go_home_button = ttk.Button(header_frame, text="🏠 Home", command=go_home, style='TButton')
go_home_button.pack(side=tk.RIGHT, padx=8)

# --- Canvas for scrollable content ---
main_canvas = tk.Canvas(root, bg=BACKGROUND_COLOR, highlightthickness=0)
main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# --- Scrollbar for the canvas ---
scrollbar_y = ttk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
main_canvas.configure(yscrollcommand=scrollbar_y.set)

# --- Content Frame (placed inside canvas) ---
content_frame = tk.Frame(main_canvas, bg=BACKGROUND_COLOR, padx=15, pady=15)
canvas_frame_id = main_canvas.create_window((0, 0), window=content_frame, anchor="nw")

content_frame.bind("<Configure>", lambda event, canvas=main_canvas: canvas.configure(scrollregion=canvas.bbox("all")))

def _on_canvas_configure(event):
    main_canvas.itemconfig(canvas_frame_id, width=event.width)

main_canvas.bind("<Configure>", _on_canvas_configure)

content_frame.grid_columnconfigure(0, weight=0)
content_frame.grid_columnconfigure(1, weight=1)
content_frame.grid_rowconfigure(0, weight=1)

# --- Left Panel for Input and Calendar ---
left_panel = tk.Frame(content_frame, bg=BACKGROUND_COLOR, padx=10, pady=10, bd=2, relief="groove")
left_panel.grid(row=0, column=0, sticky='ns', padx=8, pady=8)

tk.Label(left_panel, text="🗓️ Schedule New Appointment", font=SUBHEADER_FONT, fg=PRIMARY_COLOR, bg=BACKGROUND_COLOR).pack(pady=(8, 15)) # Increased pady

tk.Label(left_panel, text="Name:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=NORMAL_FONT).pack(anchor='w', padx=5, pady=(4, 0))
name_entry = ttk.Entry(left_panel, font=NORMAL_FONT, width=30) # Increased width
name_entry.pack(pady=(0, 10), padx=5, fill='x')

# Add Phone Number Entry
tk.Label(left_panel, text="Phone Number:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=NORMAL_FONT).pack(anchor='w', padx=5, pady=(4, 0))
phone_entry = ttk.Entry(left_panel, font=NORMAL_FONT, width=30) # Increased width
phone_entry.pack(pady=(0, 10), padx=5, fill='x')

tk.Label(left_panel, text="Select Date:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=NORMAL_FONT).pack(anchor='w', padx=5, pady=(4, 0))
calendar = Calendar(left_panel, selectmode="day", date_pattern="mm/dd/yy",
                    background=PRIMARY_COLOR, foreground='white',
                    headersbackground=ACCENT_COLOR, normalbackground='white',
                    font=NORMAL_FONT, borderwidth=1, relief="ridge")
calendar.pack(pady=(0, 10), padx=5, fill='x')
calendar.bind("<<CalendarSelected>>", on_calendar_select)

# --- Start Time Spinboxes ---
tk.Label(left_panel, text="Start Time:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=NORMAL_FONT).pack(anchor='w', padx=5, pady=(4, 0))
start_time_frame = tk.Frame(left_panel, bg=BACKGROUND_COLOR)
start_time_frame.pack(pady=(0, 10), padx=5, fill='x', expand=False)

start_hour_spinbox = ttk.Spinbox(start_time_frame, from_=0, to=23, wrap=True, width=4, format="%02.0f", font=NORMAL_FONT)
start_hour_spinbox.set(9)
start_hour_spinbox.pack(side=tk.LEFT, padx=(0, 5)) # Increased padx
tk.Label(start_time_frame, text=":", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=NORMAL_FONT).pack(side=tk.LEFT)
start_minute_spinbox = ttk.Spinbox(start_time_frame, from_=0, to=59, wrap=True, width=4, format="%02.0f", font=NORMAL_FONT)
start_minute_spinbox.set(0)
start_minute_spinbox.pack(side=tk.LEFT, padx=(5, 0)) # Increased padx

# --- End Time Spinboxes ---
tk.Label(left_panel, text="End Time:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=NORMAL_FONT).pack(anchor='w', padx=5, pady=(4, 0))
end_time_frame = tk.Frame(left_panel, bg=BACKGROUND_COLOR)
end_time_frame.pack(pady=(0, 15), padx=5, fill='x', expand=False) # Increased pady

end_hour_spinbox = ttk.Spinbox(end_time_frame, from_=0, to=23, wrap=True, width=4, format="%02.0f", font=NORMAL_FONT)
end_hour_spinbox.set(10)
end_hour_spinbox.pack(side=tk.LEFT, padx=(0, 5)) # Increased padx
tk.Label(end_time_frame, text=":", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=NORMAL_FONT).pack(side=tk.LEFT)
end_minute_spinbox = ttk.Spinbox(end_time_frame, from_=0, to=59, wrap=True, width=4, format="%02.0f", font=NORMAL_FONT)
end_minute_spinbox.set(0)
end_minute_spinbox.pack(side=tk.LEFT, padx=(5, 0)) # Increased padx

# Add Note Text Area
tk.Label(left_panel, text="Note:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=NORMAL_FONT).pack(anchor='w', padx=5, pady=(4, 0))
note_text = tk.Text(left_panel, font=NORMAL_FONT, width=30, height=5, wrap="word", bd=2, relief="groove") # Increased width and height
note_text.pack(pady=(0, 15), padx=5, fill='x', expand=False)


# Buttons Frame inside Left Panel
button_frame = tk.Frame(left_panel, bg=BACKGROUND_COLOR, pady=10) # Increased pady
button_frame.pack(fill='x', expand=False)
ttk.Button(button_frame, text="➕ Save Appointment", command=save_data, style='TButton').pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill='x') # Increased padx/pady
ttk.Button(button_frame, text="📊 Export to Excel", command=export_to_excel, style='TButton').pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill='x') # Increased padx/pady

# --- Right Panel for Displays (Treeviews and Gantt Chart) ---
right_panel = tk.Frame(content_frame, bg=BACKGROUND_COLOR, padx=10, pady=10)
right_panel.grid(row=0, column=1, sticky='nsew', padx=8, pady=8)

right_panel.grid_rowconfigure(1, weight=1)
right_panel.grid_rowconfigure(3, weight=1)
right_panel.grid_rowconfigure(5, weight=2)
right_panel.grid_columnconfigure(0, weight=1)

# Upcoming Appointments Section
tk.Label(right_panel, text="⏳ Upcoming Appointments", font=SUBHEADER_FONT, fg=PRIMARY_COLOR, bg=BACKGROUND_COLOR).grid(row=0, column=0, pady=(8, 10), sticky='ew') # Increased pady

# Filter controls for Upcoming Appointments
upcoming_filter_frame = tk.Frame(right_panel, bg=BACKGROUND_COLOR)
upcoming_filter_frame.grid(row=1, column=0, sticky='ew', padx=4, pady=(0, 8)) # Increased pady

tk.Label(upcoming_filter_frame, text="Filter by Name:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=NORMAL_FONT).pack(side=tk.LEFT, padx=(0, 8)) # Increased padx
upcoming_filter_entry = ttk.Entry(upcoming_filter_frame, font=NORMAL_FONT, width=25) # Increased width
upcoming_filter_entry.pack(side=tk.LEFT, expand=True, fill='x', padx=(0, 8)) # Increased padx
upcoming_filter_entry.bind("<KeyRelease>", apply_upcoming_filter)

upcoming_filter_button = ttk.Button(upcoming_filter_frame, text="🔍 Filter", command=apply_upcoming_filter, style='TButton')
upcoming_filter_button.pack(side=tk.LEFT)


upcoming_tree_frame = tk.Frame(right_panel, bg=BACKGROUND_COLOR, bd=2, relief="solid")
upcoming_tree_frame.grid(row=2, column=0, pady=(0, 15), padx=4, sticky='nsew') # Increased pady

upcoming_scroll = ttk.Scrollbar(upcoming_tree_frame, orient="vertical")
upcoming_scroll.pack(side="right", fill="y")
upcoming_tree = ttk.Treeview(upcoming_tree_frame, columns=("Date", "Name", "StartTime", "EndTime", "Phone", "Note"), show="headings", yscrollcommand=upcoming_scroll.set)
upcoming_tree.heading("Date", text="Date")
upcoming_tree.heading("Name", text="Name")
upcoming_tree.heading("StartTime", text="Start Time")
upcoming_tree.heading("EndTime", text="End Time")
upcoming_tree.heading("Phone", text="Phone")
upcoming_tree.heading("Note", text="Note")

upcoming_tree.column("Date", anchor="center", width=90) # Increased width
upcoming_tree.column("Name", anchor="w", width=120) # Increased width
upcoming_tree.column("StartTime", anchor="center", width=70) # Increased width
upcoming_tree.column("EndTime", anchor="center", width=70) # Increased width
upcoming_tree.column("Phone", anchor="center", width=100) # Increased width
upcoming_tree.column("Note", anchor="w", width=180) # Increased width
upcoming_tree.pack(fill='both', expand=True)
upcoming_scroll.config(command=upcoming_tree.yview)

# Current Day Appointments Section (Treeview)
tk.Label(right_panel, text="📅 Appointments for Selected Date", font=SUBHEADER_FONT, fg=PRIMARY_COLOR, bg=BACKGROUND_COLOR).grid(row=3, column=0, pady=(8, 10), sticky='ew') # Increased pady

filter_frame = tk.Frame(right_panel, bg=BACKGROUND_COLOR)
filter_frame.grid(row=4, column=0, sticky='ew', padx=4, pady=(0, 8)) # Increased pady

tk.Label(filter_frame, text="Filter by Name:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=NORMAL_FONT).pack(side=tk.LEFT, padx=(0, 8)) # Increased padx
filter_entry = ttk.Entry(filter_frame, font=NORMAL_FONT, width=25) # Increased width
filter_entry.pack(side=tk.LEFT, expand=True, fill='x', padx=(0, 8)) # Increased padx
filter_entry.bind("<KeyRelease>", apply_filter)

filter_button = ttk.Button(filter_frame, text="🔍 Filter", command=apply_filter, style='TButton')
filter_button.pack(side=tk.LEFT)

tree_frame = tk.Frame(right_panel, bg=BACKGROUND_COLOR, bd=2, relief="solid")
tree_frame.grid(row=5, column=0, pady=(0, 15), padx=4, sticky='nsew') # Increased pady

tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
tree_scroll.pack(side="right", fill="y")
tree = ttk.Treeview(tree_frame, columns=("Name", "Date", "StartTime", "EndTime", "Phone", "Note"), show="headings", yscrollcommand=tree_scroll.set)
tree.heading("Name", text="Name")
tree.heading("Date", text="Date")
tree.heading("StartTime", text="Start Time")
tree.heading("EndTime", text="End Time")
tree.heading("Phone", text="Phone")
tree.heading("Note", text="Note")

tree.column("Name", anchor="w", width=120) # Increased width
tree.column("Date", anchor="center", width=90) # Increased width
tree.column("StartTime", anchor="center", width=70) # Increased width
tree.column("EndTime", anchor="center", width=70) # Increased width
tree.column("Phone", anchor="center", width=100) # Increased width
tree.column("Note", anchor="w", width=180) # Increased width
tree.pack(fill='both', expand=True)
tree_scroll.config(command=tree.yview)

# Gantt Chart Frame
tk.Label(right_panel, text="📊 Daily Appointment Gantt Chart", font=SUBHEADER_FONT, fg=PRIMARY_COLOR, bg=BACKGROUND_COLOR).grid(row=6, column=0, pady=(8, 10), sticky='ew') # Increased pady
chart_frame = tk.Frame(right_panel, bg=BACKGROUND_COLOR, bd=2, relief="solid")
chart_frame.grid(row=7, column=0, pady=(0, 8), padx=4, sticky='nsew') # Increased pady

tk.Label(chart_frame, text="Select a date from the calendar to view its schedule.",
         bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=SUBHEADER_FONT).pack(pady=20)


# =============================================================================
# --- 4. Initial Data Load & Main Loop ---
# =============================================================================
load_upcoming(filter_name="")
load_data(selected_date=None)

root.mainloop()