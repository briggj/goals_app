# Required packages:
# pip install customtkinter
# pip install tkcalendar

import customtkinter as ctk
import json
import os
from datetime import date, datetime
import random
from tkcalendar import DateEntry
import tkinter.messagebox as messagebox

# MAX_GOALS = 10
DATA_FILE = "goals_data.json"
SETTINGS_FILE = "settings.json"

ENCOURAGING_WORDS = [
    "You've got this!", "Keep going strong!", "Amazing progress!", "One day at a time!",
    "You're doing great!", "Stay focused!", "Incredible work!", "Persistence pays off!",
    "Keep pushing forward!", "Celebrate this milestone!", "Look how far you've come!",
    "Keep up the momentum!", "Fantastic effort!", "You're inspiring!",
    "Badass milestone!", "Kick that habit's ass!", "QUIET! Silence the weakness!",
    "No mercy on cravings!", "Fear does not exist in this dojo!", "Defeat does not exist!",
    "Get your head out of your ass and keep fighting!", "Stop being a pussy, you got this!",
    "Man up and crush this!", "You're becoming a badass!", "Strike hard against temptation!",
    "Don't let weakness sweep the leg!", "Finish it! Stay strong!",
    "This shit ain't easy, but you're doing it!", "Awesome!", "Be a badass today!", "No fear!",
]

STATUS_CLEAR_DELAY_MS = 5000
DEFAULT_FONT_SIZE = 16
MIN_FONT_SIZE = 12
MAX_FONT_SIZE = 24
FONT_SIZE_INCREMENT = 2
AVAILABLE_FONT_SIZES = [str(s) for s in range(MIN_FONT_SIZE, MAX_FONT_SIZE + 1, FONT_SIZE_INCREMENT)]
DATE_ENTRY_PATTERN = 'dd-mm-y'
DISPLAY_DATE_FORMAT = "%d %b %Y"
WINDOW_RESIZE_PADDING_WIDTH = 60
WINDOW_RESIZE_PADDING_HEIGHT = 60

def calculate_time_elapsed(start_date_str):
    try:
        start_date = date.fromisoformat(start_date_str)
        today = date.today()
        delta = today - start_date
        total_days = delta.days

        if total_days < 0:
            return f"Date {start_date_str} is in the future.", total_days

        years = total_days // 365
        remaining_days = total_days % 365
        days = remaining_days

        parts = []
        if years > 0:
            parts.append(f"{years} year{'s' if years > 1 else ''}")
        if days > 0 or total_days == 0:
             parts.append(f"{days} day{'s' if days != 1 else ''}")

        if total_days == 0:
             return "Today is the day!", total_days
        elif not parts:
             return f"{total_days} day{'s' if total_days != 1 else ''} ago", total_days
        else:
             time_str = ', '.join(parts)
             return f"{time_str} ago", total_days

    except ValueError:
        return "Invalid Stored Date Format", None
    except Exception as e:
        print(f"Error calculating time for '{start_date_str}': {e}")
        return "Error calculating time", None

def get_random_encouragement():
    return random.choice(ENCOURAGING_WORDS)

class GoalsApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Goals! - Keep Track & Stay Motivated")

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.goals = []
        self.status_clear_job = None
        self.current_font_size = DEFAULT_FONT_SIZE

        self.REGULAR_FONT = None
        self.INPUT_FONT = None
        self.BUTTON_FONT = None
        self.INFO_DISPLAY_FONT = None
        self.STATUS_FONT = None
        self.FRAME_LABEL_FONT = None

        self.load_settings()
        self._update_font_tuples(self.current_font_size)

        self.load_goals()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)

        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)
        self.label_goal = ctk.CTkLabel(self.input_frame, text="Goal/Habit:", font=self.REGULAR_FONT)
        self.label_goal.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")
        self.entry_goal = ctk.CTkEntry(self.input_frame, placeholder_text="e.g., Quit Caffeine", font=self.INPUT_FONT)
        self.entry_goal.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.entry_goal.bind("<Return>", lambda event: self.date_picker.focus_set())
        self.label_date = ctk.CTkLabel(self.input_frame, text="Start/Quit Date:", font=self.REGULAR_FONT)
        self.label_date.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="w")
        self.date_picker = DateEntry(
            self.input_frame, width=15, date_pattern=DATE_ENTRY_PATTERN,
            font=self.INPUT_FONT, borderwidth=2,
        )
        self.date_picker.grid(row=1, column=1, padx=5, pady=10, sticky="w")
        self.add_button = ctk.CTkButton(self.input_frame, text="Add Goal", command=self.add_goal, font=self.BUTTON_FONT)
        self.add_button.grid(row=0, column=2, rowspan=2, padx=(5, 10), pady=10, sticky="ns")

        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.settings_frame.grid_columnconfigure(0, weight=0)
        self.settings_frame.grid_columnconfigure(1, weight=0)
        self.label_font_size = ctk.CTkLabel(self.settings_frame, text="Font Size:", font=self.REGULAR_FONT)
        self.label_font_size.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
        self.font_size_combobox = ctk.CTkComboBox(
            self.settings_frame, values=AVAILABLE_FONT_SIZES,
            command=self.font_size_changed, font=self.INPUT_FONT, state="readonly"
        )
        self.font_size_combobox.set(str(self.current_font_size))
        self.font_size_combobox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.display_frame_container = ctk.CTkFrame(self)
        self.display_frame_container.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.display_frame_container.grid_rowconfigure(0, weight=1)
        self.display_frame_container.grid_columnconfigure(0, weight=1)
        self.display_frame = ctk.CTkScrollableFrame(
            self.display_frame_container, label_text="Your Goals (Sorted by Date)",
            label_font=self.FRAME_LABEL_FONT
        )
        self.display_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.display_frame.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray", font=self.STATUS_FONT)
        self.status_label.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.update_display()
        self._adjust_window_size() 

    def _update_font_tuples(self, base_size):
        info_size = base_size + 2
        status_size = base_size - 2 if base_size > MIN_FONT_SIZE else MIN_FONT_SIZE
        frame_label_size = base_size
        self.REGULAR_FONT = ("", base_size)
        self.INPUT_FONT = ("", base_size)
        self.BUTTON_FONT = ("", base_size)
        self.INFO_DISPLAY_FONT = ("", info_size)
        self.STATUS_FONT = ("", status_size)
        self.FRAME_LABEL_FONT = ("", frame_label_size, "bold")

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings_data = json.load(f)
                    loaded_size = settings_data.get("font_size", DEFAULT_FONT_SIZE)
                    if MIN_FONT_SIZE <= loaded_size <= MAX_FONT_SIZE:
                         self.current_font_size = loaded_size
                    else:
                         self.current_font_size = DEFAULT_FONT_SIZE
            else:
                 self.current_font_size = DEFAULT_FONT_SIZE
        except Exception as e:
             print(f"Error loading settings: {e}. Using default.")
             self.current_font_size = DEFAULT_FONT_SIZE

    def save_settings(self):
        settings_data = {"font_size": self.current_font_size}
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings_data, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
            self.update_status(f"Error saving settings: {e}", "red")

    def font_size_changed(self, selected_size_str):
        try:
            new_size = int(selected_size_str)
            if MIN_FONT_SIZE <= new_size <= MAX_FONT_SIZE:
                if new_size != self.current_font_size:
                    self.current_font_size = new_size
                    self._update_font_tuples(self.current_font_size)
                    self._apply_global_font_settings() 
                    self.save_settings()
            else:
                 self.font_size_combobox.set(str(self.current_font_size))
        except ValueError:
             self.font_size_combobox.set(str(self.current_font_size))

    def _apply_global_font_settings(self):
        self.label_goal.configure(font=self.REGULAR_FONT)
        self.entry_goal.configure(font=self.INPUT_FONT)
        self.label_date.configure(font=self.REGULAR_FONT)
        self.add_button.configure(font=self.BUTTON_FONT)
        self.label_font_size.configure(font=self.REGULAR_FONT)
        self.font_size_combobox.configure(font=self.INPUT_FONT)
        self.status_label.configure(font=self.STATUS_FONT)
        self.display_frame.configure(label_font=self.FRAME_LABEL_FONT)
        try:
            self.date_picker.configure(font=self.INPUT_FONT, date_pattern=DATE_ENTRY_PATTERN)
        except Exception as e:
            print(f"Note: Could not apply font/pattern to DatePicker: {e}")

        self.update_display()
        self._adjust_window_size()

    def _adjust_window_size(self):
        self.update_idletasks()

        req_width = self.winfo_reqwidth()
        req_height = self.winfo_reqheight()

        padded_width = req_width + WINDOW_RESIZE_PADDING_WIDTH
        padded_height = req_height + WINDOW_RESIZE_PADDING_HEIGHT

        self.minsize(padded_width, padded_height)
        self.geometry(f"{padded_width}x{padded_height}")
        print(f"Resized window to: {padded_width}x{padded_height} (Min Required: {req_width}x{req_height})") 

    def load_goals(self):
        load_error = False
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.goals = json.load(f)
            except json.JSONDecodeError:
                self.update_status(f"Warning: Could not read {DATA_FILE}. Starting fresh.", "orange", persistent=True)
                self.goals = []
                load_error = True
            except Exception as e:
                self.update_status(f"Error loading goals: {e}", "red", persistent=True)
                self.goals = []
                load_error = True
        else:
            self.goals = []
        for goal in self.goals:
            goal['_current_encouragement'] = get_random_encouragement()
        if not load_error and not self.goals:
             pass
        elif not load_error:
             pass

    def save_goals(self):
        try:
            self.goals.sort(key=lambda x: x.get('date', '9999-12-31'))
            with open(DATA_FILE, 'w') as f:
                json.dump(self.goals, f, indent=4)
        except Exception as e:
            print(f"Error saving goals: {e}")
            self.update_status(f"Error saving goals: {e}", "red", persistent=True)

    def update_display(self):
        for widget in self.display_frame.winfo_children():
            widget.destroy()

        if not self.goals:
            no_goals_label = ctk.CTkLabel(self.display_frame, text="No goals added yet...", font=self.INFO_DISPLAY_FONT)
            no_goals_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        try:
            self.goals.sort(key=lambda x: date.fromisoformat(x.get('date', '9999-12-31')))
        except ValueError:
             self.update_status("Warning: Invalid date found during sorting.", "orange")
             self.goals.sort(key=lambda x: x.get('date', '9999-12-31'))

        for index, goal in enumerate(self.goals):
            goal_name = goal.get('name', 'Unnamed')
            goal_date_str_iso = goal.get('date', 'No Date')
            try:
                date_obj = date.fromisoformat(goal_date_str_iso)
                display_date_str = date_obj.strftime(DISPLAY_DATE_FORMAT).upper() 
            except ValueError:
                display_date_str = goal_date_str_iso + " (invalid)"

            elapsed_str, _ = calculate_time_elapsed(goal_date_str_iso)
            encouragement = goal.get('_current_encouragement', get_random_encouragement())

            item_frame = ctk.CTkFrame(self.display_frame)
            item_frame.grid(row=index, column=0, padx=5, pady=(3, 4), sticky="ew")
            item_frame.grid_columnconfigure(0, weight=1)
            item_frame.grid_columnconfigure(1, weight=0)
            item_frame.grid_columnconfigure(2, weight=0)

            info_text = f"📌 {goal_name} (Since: {display_date_str})\n   └── {elapsed_str} - {encouragement}"

            info_label = ctk.CTkLabel(item_frame, text=info_text, justify="left", anchor="w", font=self.INFO_DISPLAY_FONT)
            info_label.grid(row=0, column=0, padx=10, pady=(5,5), sticky="ew")

            edit_button = ctk.CTkButton(
                item_frame, text="Edit", command=lambda i=index: self.open_edit_dialog(i),
                width=50, font=self.BUTTON_FONT, fg_color="#3B8ED0", hover_color="#2F70A6"
            )
            edit_button.grid(row=0, column=1, padx=(5, 5), pady=5, sticky="e")

            delete_button = ctk.CTkButton(
                item_frame, text="Delete", command=lambda i=index: self.delete_goal(i),
                width=60, fg_color="#DB3E3E", hover_color="#A92F2F", font=self.BUTTON_FONT
            )
            delete_button.grid(row=0, column=2, padx=(0, 10), pady=5, sticky="e")


    def add_goal(self):
        goal_name = self.entry_goal.get().strip()
        try:
            goal_date_obj = self.date_picker.get_date()
            goal_date_str_iso = goal_date_obj.isoformat()
        except Exception as e:
             print(f"Error getting date from picker: {e}")
             self.update_status("Could not get date from picker.", "red")
             return
        if not goal_name:
            self.update_status("Goal name cannot be empty.", "orange")
            self.entry_goal.focus_set()
            return
        for existing_goal in self.goals:
            if existing_goal.get('name', '').lower() == goal_name.lower():
                 self.update_status(f"Goal '{goal_name}' already exists.", "orange")
                 return
#        if len(self.goals) >= MAX_GOALS:
#            self.update_status(f"Cannot add more than {MAX_GOALS} goals.", "orange")
#            return
        new_goal = {"name": goal_name, "date": goal_date_str_iso}
        new_goal['_current_encouragement'] = get_random_encouragement()
        self.goals.append(new_goal)
        self.save_goals()
        self.update_display()
        self.entry_goal.delete(0, ctk.END)
        self.date_picker.set_date(date.today())
        self.entry_goal.focus_set()
        self.update_status(f"Goal '{goal_name}' added successfully!", "green")

    def delete_goal(self, index):
        goal_to_delete = self.goals[index].get('name', 'this goal')
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the goal '{goal_to_delete}'?"):
            if 0 <= index < len(self.goals):
                try:
                    removed_goal = self.goals.pop(index)
                    self.save_goals()
                    self.update_display()
                    self.update_status(f"Goal '{removed_goal.get('name', 'Unknown')}' deleted.", "#A9A9A9")
                except Exception as e:
                    self.update_status(f"Error deleting goal: {e}", "red")
                    self.update_display()
            else:
                self.update_status("Error: Could not delete goal (invalid index).", "red")

    def update_status(self, message, color="gray", persistent=False):
        self.status_label.configure(text=message, text_color=color)
        if self.status_clear_job:
            self.status_label.after_cancel(self.status_clear_job)
            self.status_clear_job = None
        if color != "red" or not persistent:
            self.status_clear_job = self.status_label.after(
                STATUS_CLEAR_DELAY_MS,
                lambda: self.status_label.configure(text="")
            )

    def open_edit_dialog(self, index):
        if not (0 <= index < len(self.goals)):
            self.update_status("Error: Cannot edit goal (invalid index).", "red")
            return
        goal_data = self.goals[index]
        original_name = goal_data.get('name', '')
        original_date_str_iso = goal_data.get('date', '')
        edit_dialog = ctk.CTkToplevel(self)
        edit_dialog.title("Edit Goal")
        edit_dialog.transient(self)
        edit_dialog.grab_set()
        edit_dialog.geometry("400x250") 
        dialog_frame = ctk.CTkFrame(edit_dialog)
        dialog_frame.pack(expand=True, fill="both", padx=20, pady=20)
        name_label = ctk.CTkLabel(dialog_frame, text="Goal Name:", font=self.REGULAR_FONT)
        name_label.grid(row=0, column=0, padx=5, pady=(5, 5), sticky="w")
        name_entry = ctk.CTkEntry(dialog_frame, font=self.INPUT_FONT, width=250)
        name_entry.insert(0, original_name)
        name_entry.grid(row=0, column=1, padx=5, pady=(5, 5), sticky="ew")
        date_label = ctk.CTkLabel(dialog_frame, text="Start/Quit Date:", font=self.REGULAR_FONT)
        date_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        try:
            initial_date = date.fromisoformat(original_date_str_iso)
        except ValueError:
            print(f"Warning: Invalid date format '{original_date_str_iso}' for goal '{original_name}'. Defaulting.")
            initial_date = date.today()
        edit_date_picker = DateEntry(
            dialog_frame, width=15, date_pattern=DATE_ENTRY_PATTERN, 
            font=self.INPUT_FONT, borderwidth=2,
        )
        edit_date_picker.set_date(initial_date)
        edit_date_picker.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        dialog_status_label = ctk.CTkLabel(dialog_frame, text="", font=self.STATUS_FONT, text_color="orange")
        dialog_status_label.grid(row=2, column=0, columnspan=2, padx=5, pady=(10, 0), sticky="ew")
        button_frame = ctk.CTkFrame(dialog_frame, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, pady=(20, 5))
        save_button = ctk.CTkButton(
            button_frame, text="Save Changes", font=self.BUTTON_FONT,
            command=lambda: self.save_edit(index, name_entry, edit_date_picker, edit_dialog, dialog_status_label)
        )
        save_button.pack(side="left", padx=10)
        cancel_button = ctk.CTkButton(
            button_frame, text="Cancel", font=self.BUTTON_FONT, fg_color="gray", hover_color="darkgray",
            command=edit_dialog.destroy
        )
        cancel_button.pack(side="right", padx=10)
        name_entry.focus_set()
        edit_dialog.bind("<Return>", lambda event: save_button.invoke())
        edit_dialog.bind("<Escape>", lambda event: edit_dialog.destroy())

    def save_edit(self, index, name_widget, date_widget, dialog, status_widget):
        new_name = name_widget.get().strip()
        try:
            new_date_obj = date_widget.get_date()
            new_date_str_iso = new_date_obj.isoformat() 
        except Exception as e:
            print(f"Error getting date from edit picker: {e}")
            status_widget.configure(text="Error getting date.", text_color="red")
            return
        if not new_name:
            status_widget.configure(text="Goal name cannot be empty.")
            return
        for i, goal in enumerate(self.goals):
            if i != index and goal.get('name', '').lower() == new_name.lower():
                status_widget.configure(text=f"Another goal named '{new_name}' already exists.")
                return
        try:
            self.goals[index]['name'] = new_name
            self.goals[index]['date'] = new_date_str_iso
            self.save_goals()
            self.update_display()
            self.update_status(f"Goal '{new_name}' updated successfully.", "green")
            dialog.destroy()
        except Exception as e:
            print(f"Error saving edited goal: {e}")
            status_widget.configure(text=f"Error saving changes: {e}", text_color="red")
            self.update_status(f"Error saving changes for goal index {index}.", "red")

if __name__ == "__main__":
    app = GoalsApp()
    app.mainloop()