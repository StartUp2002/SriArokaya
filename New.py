import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import pandas as pd
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure 

# --- Constants and Initial Setup ---
FILE_NAME = "data.csv"
APP_TITLE = "Thai Traditional Massage Queue System"
PRIMARY_COLOR = "#2C3E50"  # Dark Blue/Grey for main elements
ACCENT_COLOR = "#3498DB"   # Bright Blue for highlights/buttons
BACKGROUND_COLOR = "#ECF0F1" # Light Grey for general background
TEXT_COLOR = "#2C3E50"      # Dark text
HEADER_FONT = ("Arial", 16, "bold") # Reduced header font size slightly
SUBHEADER_FONT = ("Arial", 12, "bold") # Reduced subheader font size slightly
NORMAL_FONT = ("Arial", 9) # Reduced normal font size
BUTTON_FONT = ("Arial", 9, "bold") # Reduced button font size

# Ensure the data file exists
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["Name", "Date", "StartTime", "EndTime"])
    df.to_csv(FILE_NAME, index=False)

# --- Core Functions ---

def save_data():
    """Saves new appointment data to the CSV file, with validation."""
    name = name_entry.get().strip()
    start = start_entry.get().strip()
    end = end_entry.get().strip()
    
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
        messagebox.showerror("Error", "Invalid time format. Please use HH:MM (e.g., 10:00).")
        return

    df = pd.read_csv(FILE_NAME)
    
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

    new_row = pd.DataFrame([[name, date_formatted, start, end]], columns=["Name", "Date", "StartTime", "EndTime"])
    new_row.to_csv(FILE_NAME, mode='a', header=False, index=False)
    messagebox.showinfo("Success", "Appointment saved!")

    name_entry.delete(0, tk.END)
    start_entry.delete(0, tk.END)
    end_entry.delete(0, tk.END)

    load_data(selected_date=date_formatted)
    load_upcoming()

def load_data(selected_date=None):
    """Loads appointment data into the main Treeview and draws Gantt chart."""
    for row in tree.get_children():
        tree.delete(row)
    try:
        df = pd.read_csv(FILE_NAME)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        df_filtered = df[df["Date"] == selected_date] if selected_date else df.copy() 
        
        for _, row in df_filtered.iterrows():
            tree.insert("", "end", values=list(row[["Name", "Date", "StartTime", "EndTime"]])) 
        
        if selected_date:
            draw_gantt_chart(df_filtered, selected_date)
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
    
    load_upcoming() 

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

    # Further adjusted figsize and dpi for even smaller chart
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
        
        # Adjusted text_x_pos and fontsize for smaller chart
        text_x_pos = start_minute_of_day + 5 
        ax.text(text_x_pos, i, f"{row['Name']} ({start.strftime('%H:%M')}-{end.strftime('%H:%M')})", 
                va='center', ha='left', color='black', fontsize=7, weight='bold') # Further reduced fontsize
    
    # Keeping xlim for 24 hours
    ax.set_xlim(0, 1440) 
    
    major_ticks = range(0, 1441, 60)
    minor_ticks = range(0, 1441, 30)
    ax.set_xticks(major_ticks)
    ax.set_xticks(minor_ticks, minor=True)
    
    ax.set_xticklabels([f"{h:02d}:00" for h in range(25)], fontsize=8) # Reduced xticklabel fontsize
    
    ax.set_yticks([]) 
    ax.invert_yaxis() 
    
    ax.set_xlabel("Time of Day", fontsize=8, color=TEXT_COLOR) # Reduced xlabel fontsize
    ax.set_title(f"Appointment Schedule for {selected_date}", fontsize=12, color=PRIMARY_COLOR, weight='bold') # Reduced title fontsize
    
    ax.xaxis.grid(True, which='major', linestyle='--', linewidth=0.5, color='gray', alpha=0.7)
    ax.xaxis.grid(True, which='minor', linestyle=':', linewidth=0.3, color='gray', alpha=0.5)
    ax.set_facecolor("lightgray") 
    
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill='both', expand=True, padx=5, pady=2) # Further reduced padx, pady
    
    root._gantt_canvas = canvas 

def export_to_excel():
    """Exports all appointment data to an Excel file."""
    try:
        df = pd.read_csv(FILE_NAME)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df.to_excel("Appointment_Schedule.xlsx", index=False)
        messagebox.showinfo("Success", "Exported to 'Appointment_Schedule.xlsx'")
    except Exception as e:
        messagebox.showerror("Export Failed", f"Export failed: {e}")

def on_calendar_select(event=None): 
    """Callback when a date is selected on the calendar."""
    try:
        selected_date = datetime.strptime(calendar.get_date(), "%m/%d/%y").strftime("%Y-%m-%d")
        root.title(f"{APP_TITLE} | Appointments for {selected_date}")
        load_data(selected_date=selected_date)
    except ValueError as e:
        messagebox.showerror("Error", f"Invalid date format from calendar: {calendar.get_date()}. Please select a date. Error: {e}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred during date selection:\n{e}")

def load_upcoming():
    """Loads and displays upcoming appointments in a separate Treeview."""
    for row in upcoming_tree.get_children():
        upcoming_tree.delete(row)
    try:
        df = pd.read_csv(FILE_NAME)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        
        df["StartDatetime"] = pd.to_datetime(df["Date"] + " " + df["StartTime"])
        df["EndDatetime"] = pd.to_datetime(df["Date"] + " " + df["EndTime"])
        now = datetime.now()
        
        df = df[df["EndDatetime"] >= now] 
        df = df.sort_values(by="StartDatetime")
        
        for _, row in df.iterrows():
            upcoming_tree.insert("", "end", values=[
                row["Date"],
                row["Name"],
                row["StartTime"],
                row["EndTime"]
            ])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load upcoming appointments:\n{e}")

def go_home():
    """Resets the view to show all appointments and the main title."""
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


# --- GUI Setup ---
root = tk.Tk()
root.title(f"Home | {APP_TITLE}")
# กำหนดขนาดเริ่มต้นของหน้าต่างให้เล็กลงอีก
root.geometry("1000x700") 
root.configure(bg=BACKGROUND_COLOR) 

# Style Configuration for ttk widgets
style = ttk.Style()
style.theme_use('clam') 

style.configure('TFrame', background=BACKGROUND_COLOR)
style.configure('TLabel', background=BACKGROUND_COLOR, foreground=TEXT_COLOR, font=NORMAL_FONT)
style.configure('TEntry', font=NORMAL_FONT) 

style.configure('TButton', background=ACCENT_COLOR, foreground='white', font=BUTTON_FONT, padding=6, relief='flat') # Reduced button padding
style.map('TButton', background=[('active', PRIMARY_COLOR)], foreground=[('active', 'white')]) 

style.configure('Treeview.Heading', font=SUBHEADER_FONT, background=PRIMARY_COLOR, foreground='white', padding=3) # Reduced heading padding
style.configure('Treeview', font=NORMAL_FONT, rowheight=24, background='white', foreground=TEXT_COLOR, fieldbackground='white') # Reduced rowheight
style.map('Treeview', background=[('selected', ACCENT_COLOR)])

# --- Main Scrollable Canvas Setup ---
# Create a Canvas for scrolling
main_canvas = tk.Canvas(root, bg=BACKGROUND_COLOR, highlightthickness=0)
main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create Vertical Scrollbar
v_scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=main_canvas.yview)
v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
main_canvas.configure(yscrollcommand=v_scrollbar.set)

# Create Horizontal Scrollbar
h_scrollbar = ttk.Scrollbar(root, orient=tk.HORIZONTAL, command=main_canvas.xview)
h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X) 
main_canvas.configure(xscrollcommand=h_scrollbar.set) 

# Create a Frame inside the Canvas to hold all your content
scrollable_frame = tk.Frame(main_canvas, bg=BACKGROUND_COLOR)
# Add the frame to a window in the canvas
main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

# Function to update the scroll region
def on_frame_configure(event):
    # Update the scrollregion of the canvas when the size of the frame changes
    main_canvas.configure(scrollregion=main_canvas.bbox("all"))
    # Additionally, ensure the canvas's width is at least the width of the frame if not expanded
    # This might be causing issues with horizontal scrolling if the frame is not allowed to expand
    # Let's try to remove the specific width setting for the scrollable frame in the canvas
    # main_canvas.itemconfig(main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw"), width=scrollable_frame.winfo_reqwidth())


scrollable_frame.bind("<Configure>", on_frame_configure)

# --- Now, pack all your existing UI elements into 'scrollable_frame' instead of 'root' ---

# Header Frame (for title and Go Home button)
header_frame = tk.Frame(scrollable_frame, bg=PRIMARY_COLOR, padx=10, pady=8) # Reduced padding
header_frame.pack(fill='x', expand=False) 
tk.Label(header_frame, text=APP_TITLE, font=HEADER_FONT, fg="white", bg=PRIMARY_COLOR).pack(side=tk.LEFT, padx=8) # Reduced padx
go_home_button = ttk.Button(header_frame, text="🏠 Home", command=go_home, style='TButton')
go_home_button.pack(side=tk.RIGHT, padx=8) # Reduced padx


# Main Content Frame (holds input, calendar, and treeviews)
content_frame = tk.Frame(scrollable_frame, bg=BACKGROUND_COLOR, padx=15, pady=15) # Reduced padding
content_frame.pack(fill='both', expand=True) 

# Left Panel for Input and Calendar
left_panel = tk.Frame(content_frame, bg=BACKGROUND_COLOR, padx=10, pady=10, bd=2, relief="groove") # Reduced padding
left_panel.pack(side=tk.LEFT, fill='y', padx=8, pady=8) # Reduced padx, pady

tk.Label(left_panel, text="🗓️ Schedule New Appointment", font=SUBHEADER_FONT, fg=PRIMARY_COLOR, bg=BACKGROUND_COLOR).pack(pady=(8, 12)) # Reduced pady

tk.Label(left_panel, text="Name:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(anchor='w', padx=5, pady=(4, 0)) # Reduced pady
name_entry = ttk.Entry(left_panel, font=NORMAL_FONT, width=25) # Further reduced width
name_entry.pack(pady=(0, 8), padx=5) # Reduced pady

tk.Label(left_panel, text="Select Date:", bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(anchor='w', padx=5, pady=(4, 0)) # Reduced pady
calendar = Calendar(left_panel, selectmode="day", date_pattern="mm/dd/yy",
                    background=PRIMARY_COLOR, foreground='white',
                    headersbackground=ACCENT_COLOR, normalbackground='white',
                    font=NORMAL_FONT, borderwidth=1, relief="ridge") 
calendar.pack(pady=(0, 8), padx=5) # Reduced pady
calendar.bind("<<CalendarSelected>>", on_calendar_select)

tk.Label(left_panel, text="Start Time (HH:MM):", bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(anchor='w', padx=5, pady=(4, 0)) # Reduced pady
start_entry = ttk.Entry(left_panel, font=NORMAL_FONT, width=12) # Further reduced width
start_entry.pack(pady=(0, 8), padx=5) # Reduced pady

tk.Label(left_panel, text="End Time (HH:MM):", bg=BACKGROUND_COLOR, fg=TEXT_COLOR).pack(anchor='w', padx=5, pady=(4, 0)) # Reduced pady
end_entry = ttk.Entry(left_panel, font=NORMAL_FONT, width=12) # Further reduced width
end_entry.pack(pady=(0, 12), padx=5) # Reduced pady

# Buttons Frame
button_frame = tk.Frame(left_panel, bg=BACKGROUND_COLOR, pady=8) # Reduced pady
button_frame.pack()
ttk.Button(button_frame, text="➕ Save Appointment", command=save_data, style='TButton').pack(side=tk.LEFT, padx=4, pady=4) # Reduced padx, pady
ttk.Button(button_frame, text="📊 Export to Excel", command=export_to_excel, style='TButton').pack(side=tk.LEFT, padx=4, pady=4) # Reduced padx, pady


# Right Panel for Displays (Treeviews and Gantt Chart)
right_panel = tk.Frame(content_frame, bg=BACKGROUND_COLOR, padx=10, pady=10) # Reduced padding
right_panel.pack(side=tk.RIGHT, fill='both', expand=True, padx=8, pady=8) # Reduced padx, pady

# Upcoming Appointments Section
tk.Label(right_panel, text="⏳ Upcoming Appointments", font=SUBHEADER_FONT, fg=PRIMARY_COLOR, bg=BACKGROUND_COLOR).pack(pady=(4, 8)) # Reduced pady
upcoming_frame = tk.Frame(right_panel, bg=BACKGROUND_COLOR, bd=2, relief="solid") 
upcoming_frame.pack(pady=(0, 10), fill='x', padx=4) # Reduced pady, padx

upcoming_scroll = ttk.Scrollbar(upcoming_frame, orient="vertical")
upcoming_scroll.pack(side="right", fill="y")
upcoming_tree = ttk.Treeview(upcoming_frame, columns=("Date", "Name", "StartTime", "EndTime"), show="headings", yscrollcommand=upcoming_scroll.set, height=8) # Reduced height
for col in ("Date", "Name", "StartTime", "EndTime"):
    upcoming_tree.heading(col, text=col)
    upcoming_tree.column(col, anchor="center") 
upcoming_tree.pack(fill='x', expand=True)
upcoming_scroll.config(command=upcoming_tree.yview)


# Current Day Appointments Section (Treeview)
tk.Label(right_panel, text="📅 Appointments for Selected Date", font=SUBHEADER_FONT, fg=PRIMARY_COLOR, bg=BACKGROUND_COLOR).pack(pady=(8, 8)) # Reduced pady
tree_frame = tk.Frame(right_panel, bg=BACKGROUND_COLOR, bd=2, relief="solid") 
tree_frame.pack(pady=(0, 10), fill='x', padx=4) # Reduced pady, padx

tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
tree_scroll.pack(side="right", fill="y")
tree = ttk.Treeview(tree_frame, columns=("Name", "Date", "StartTime", "EndTime"), show="headings", yscrollcommand=tree_scroll.set, height=8) # Reduced height
for col in ("Name", "Date", "StartTime", "EndTime"):
    tree.heading(col, text=col)
    tree.column(col, anchor="center") 
tree.pack(fill='x', expand=True)
tree_scroll.config(command=tree.yview)

# Gantt Chart Frame
tk.Label(right_panel, text="📊 Daily Appointment Gantt Chart", font=SUBHEADER_FONT, fg=PRIMARY_COLOR, bg=BACKGROUND_COLOR).pack(pady=(8, 8)) # Reduced pady
chart_frame = tk.Frame(right_panel, bg=BACKGROUND_COLOR, bd=2, relief="solid") 
chart_frame.pack(pady=(0, 4), fill='both', expand=True, padx=4) # Reduced pady, padx
tk.Label(chart_frame, text="Select a date from the calendar to view its schedule.", 
         bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=SUBHEADER_FONT).pack(pady=15) # Reduced pady


# --- Initial Data Load ---
load_upcoming() 
load_data(selected_date=None) 

root.mainloop()