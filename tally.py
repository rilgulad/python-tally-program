import tkinter as tk
import os
import json
import csv
from datetime import datetime
from tkinter import messagebox, simpledialog, filedialog  # Import messagebox for confirmation

# File to save tallies
TALLY_FILE = "tallies.json"

# Load tallies from file
def load_tallies():
    if os.path.exists(TALLY_FILE):
        with open(TALLY_FILE, "r") as file:
            data = json.load(file)
            # Handle old format (backward compatibility)
            if "settings" not in data:
                # Convert old format to new format
                old_tallies = {k: v for k, v in data.items() if k not in ["history"]}
                return {
                    "settings": {
                        "counters": list(old_tallies.keys()),
                        "max_history": 2
                    },
                    "tallies": old_tallies,
                    "history": data.get("history", []),
                    "first_tally_time": None,
                    "last_tally_time": None
                }
            # Ensure the history key exists
            if "history" not in data:
                data["history"] = []
            # Ensure timestamp fields exist
            if "first_tally_time" not in data:
                data["first_tally_time"] = None
            if "last_tally_time" not in data:
                data["last_tally_time"] = None
            # Ensure undo stack exists
            if "undo_stack" not in data:
                data["undo_stack"] = []
            # Ensure max_history exists in settings
            if "max_history" not in data["settings"]:
                data["settings"]["max_history"] = 2
            # Ensure window position exists
            if "window_x" not in data["settings"]:
                data["settings"]["window_x"] = 1000
            if "window_y" not in data["settings"]:
                data["settings"]["window_y"] = 500
            # Ensure theme exists
            if "theme" not in data["settings"]:
                data["settings"]["theme"] = "light"
            # Ensure sound setting exists
            if "sound_enabled" not in data["settings"]:
                data["settings"]["sound_enabled"] = False
            return data
    # Default structure
    return {
        "settings": {
            "counters": ["Reference", "Direction"],
            "max_history": 2,
            "window_x": 1000,
            "window_y": 500,
            "theme": "light",
            "sound_enabled": False
        },
        "tallies": {
            "Reference": 0,
            "Direction": 0
        },
        "history": [],
        "first_tally_time": None,
        "last_tally_time": None,
        "undo_stack": []
    }

# Save tallies to file
def save_tallies(data):
    with open(TALLY_FILE, "w") as file:
        json.dump(data, file)

# Settings Dialog
class SettingsDialog:
    def __init__(self, parent, settings_data):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("350x550")
        self.dialog.attributes("-topmost", True)

        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Max history setting
        history_frame = tk.Frame(self.dialog)
        history_frame.pack(pady=5)
        tk.Label(history_frame, text="Max History:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        self.max_history_var = tk.IntVar(value=settings_data.get("max_history", 2))
        self.max_history_spinbox = tk.Spinbox(history_frame, from_=1, to=10, textvariable=self.max_history_var, width=5)
        self.max_history_spinbox.pack(side=tk.LEFT, padx=5)

        # Theme and Sound settings
        options_frame = tk.Frame(self.dialog)
        options_frame.pack(pady=5)
        self.theme_var = tk.StringVar(value=settings_data.get("theme", "light"))
        tk.Checkbutton(options_frame, text="Dark Mode",
                      variable=self.theme_var, onvalue="dark", offvalue="light").pack(side=tk.LEFT, padx=5)
        self.sound_var = tk.BooleanVar(value=settings_data.get("sound_enabled", False))
        tk.Checkbutton(options_frame, text="Sound Effects",
                      variable=self.sound_var).pack(side=tk.LEFT, padx=5)

        tk.Label(self.dialog, text="Counter Names:", font=('Arial', 10, 'bold')).pack(pady=5)

        # Frame for counter list
        list_frame = tk.Frame(self.dialog)
        list_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        # Scrollbar for listbox
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.counter_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=8)
        self.counter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.counter_listbox.yview)

        # Populate listbox with current counters
        for counter in settings_data.get("counters", []):
            self.counter_listbox.insert(tk.END, counter)

        # Buttons frame
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Add", command=self.add_counter, width=8).grid(row=0, column=0, padx=2)
        tk.Button(btn_frame, text="Remove", command=self.remove_counter, width=8).grid(row=0, column=1, padx=2)
        tk.Button(btn_frame, text="Rename", command=self.rename_counter, width=8).grid(row=0, column=2, padx=2)
        tk.Button(btn_frame, text="Move Up", command=self.move_up, width=8).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(btn_frame, text="Move Down", command=self.move_down, width=8).grid(row=1, column=1, padx=2, pady=2)

        # Save and Cancel buttons
        bottom_frame = tk.Frame(self.dialog)
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, text="Save", command=self.save, width=10, bg="lightgreen").grid(row=0, column=0, padx=5)
        tk.Button(bottom_frame, text="Cancel", command=self.cancel, width=10).grid(row=0, column=1, padx=5)

    def add_counter(self):
        name = simpledialog.askstring("Add Counter", "Enter counter name:", parent=self.dialog)
        if name and name.strip():
            self.counter_listbox.insert(tk.END, name.strip())

    def remove_counter(self):
        selection = self.counter_listbox.curselection()
        if selection:
            if self.counter_listbox.size() <= 1:
                messagebox.showwarning("Warning", "You must have at least one counter!", parent=self.dialog)
                return
            self.counter_listbox.delete(selection[0])

    def rename_counter(self):
        selection = self.counter_listbox.curselection()
        if selection:
            old_name = self.counter_listbox.get(selection[0])
            new_name = simpledialog.askstring("Rename Counter", f"Rename '{old_name}' to:",
                                             initialvalue=old_name, parent=self.dialog)
            if new_name and new_name.strip():
                self.counter_listbox.delete(selection[0])
                self.counter_listbox.insert(selection[0], new_name.strip())
                self.counter_listbox.selection_set(selection[0])

    def move_up(self):
        selection = self.counter_listbox.curselection()
        if selection and selection[0] > 0:
            idx = selection[0]
            item = self.counter_listbox.get(idx)
            self.counter_listbox.delete(idx)
            self.counter_listbox.insert(idx - 1, item)
            self.counter_listbox.selection_set(idx - 1)

    def move_down(self):
        selection = self.counter_listbox.curselection()
        if selection and selection[0] < self.counter_listbox.size() - 1:
            idx = selection[0]
            item = self.counter_listbox.get(idx)
            self.counter_listbox.delete(idx)
            self.counter_listbox.insert(idx + 1, item)
            self.counter_listbox.selection_set(idx + 1)

    def save(self):
        counters = list(self.counter_listbox.get(0, tk.END))
        if not counters:
            messagebox.showwarning("Warning", "You must have at least one counter!", parent=self.dialog)
            return
        max_history = self.max_history_var.get()
        if max_history < 1:
            messagebox.showwarning("Warning", "Max history must be at least 1!", parent=self.dialog)
            return
        self.result = {
            "counters": counters,
            "max_history": max_history,
            "theme": self.theme_var.get(),
            "sound_enabled": self.sound_var.get()
        }
        self.dialog.destroy()

    def cancel(self):
        self.result = None
        self.dialog.destroy()

    def show(self):
        self.dialog.wait_window()
        return self.result

class TallyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tally Counter")

        self.data = load_tallies()

        # Set window position from saved settings
        window_x = self.data["settings"].get("window_x", 1000)
        window_y = self.data["settings"].get("window_y", 500)
        self.root.geometry(f"450x550+{window_x}+{window_y}")
        self.root.attributes("-topmost", True)  # Always on top

        # Storage for dynamic widgets
        self.counter_labels = {}
        self.counter_buttons = {}
        self.counter_reset_menus = {}

        # Theme colors
        self.themes = {
            "light": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "button_bg": "#e0e0e0",
                "text_bg": "#ffffff"
            },
            "dark": {
                "bg": "#2b2b2b",
                "fg": "#ffffff",
                "button_bg": "#3c3c3c",
                "text_bg": "#1e1e1e"
            }
        }

        # Auto-save on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.build_ui()
        self.apply_theme()

    def build_ui(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        self.counter_labels.clear()
        self.counter_buttons.clear()

        current_row = 0

        # Top button row: Undo, Export, Toggle History
        top_btn_frame = tk.Frame(self.root)
        top_btn_frame.grid(row=current_row, column=0, columnspan=2, sticky='ew', padx=5, pady=2)

        tk.Button(top_btn_frame, text="Undo", command=self.undo_last_action, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(top_btn_frame, text="Export CSV", command=self.export_to_csv, width=10).pack(side=tk.LEFT, padx=2)
        tk.Button(top_btn_frame, text="Toggle History", command=self.toggle_history).pack(side=tk.LEFT, padx=2)
        current_row += 1

        # Statistics display
        self.stats_label = tk.Label(self.root, text="", font=('Arial', 9))
        self.stats_label.grid(row=current_row, column=0, columnspan=2, padx=5, pady=2)
        current_row += 1

        # History text area
        self.history_text = tk.Text(self.root, height=5, width=40, state='disabled')
        self.history_text.grid(row=current_row, column=0, columnspan=2, sticky='ew', padx=5, pady=2)
        self.history_text.grid_remove()  # Initially hidden
        current_row += 1

        # Dynamically create counters based on settings
        counters = self.data["settings"]["counters"]

        # Ensure all counters exist in tallies
        for counter in counters:
            if counter not in self.data["tallies"]:
                self.data["tallies"][counter] = 0

        for counter_name in counters:
            # Label showing current count with right-click menu
            label = tk.Label(self.root, text=f"{counter_name}: {self.data['tallies'][counter_name]}")
            label.grid(row=current_row, column=0, columnspan=2, padx=5, pady=2)
            self.counter_labels[counter_name] = label

            # Right-click menu for resetting individual counter
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label=f"Reset {counter_name}",
                           command=lambda name=counter_name: self.reset_counter(name))
            label.bind("<Button-3>", lambda e, m=menu: m.post(e.x_root, e.y_root))
            self.counter_reset_menus[counter_name] = menu
            current_row += 1

            # Buttons to add and subtract
            add_btn = tk.Button(self.root, text=f"Add to {counter_name}",
                              command=lambda name=counter_name: self.add_tally(name),
                              bg="lightgreen")
            add_btn.grid(row=current_row, column=0, sticky='ew', padx=(5, 2), pady=2)

            sub_btn = tk.Button(self.root, text=f"Subtract",
                              command=lambda name=counter_name: self.subtract_tally(name),
                              bg="lightcoral")
            sub_btn.grid(row=current_row, column=1, sticky='ew', padx=(2, 5), pady=2)

            self.counter_buttons[counter_name] = (add_btn, sub_btn)
            current_row += 1

        # Save & Quit button
        self.save_btn = tk.Button(self.root, text="Save & Quit", command=self.save_and_quit)
        self.save_btn.grid(row=current_row, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        current_row += 1

        # Clear Tallies button with confirmation
        self.clear_btn = tk.Button(self.root, text="Clear", command=self.confirm_clear,
                                   width=6, height=1, bg="red")
        self.clear_btn.grid(row=current_row, column=0, columnspan=2, sticky='e', padx=5, pady=2)
        current_row += 1

        # Settings button at the bottom
        settings_btn = tk.Button(self.root, text="Settings", command=self.open_settings)
        settings_btn.grid(row=current_row, column=0, columnspan=2, sticky='ew', padx=5, pady=2)

        self.update_history_display()
        self.update_statistics()

    def play_sound(self):
        """Play a simple beep sound if sound is enabled"""
        if self.data["settings"].get("sound_enabled", False):
            try:
                self.root.bell()
            except:
                pass  # Ignore sound errors

    def save_undo_state(self):
        """Save current state to undo stack"""
        undo_state = {
            "tallies": self.data["tallies"].copy(),
            "first_tally_time": self.data.get("first_tally_time"),
            "last_tally_time": self.data.get("last_tally_time")
        }
        self.data["undo_stack"].append(undo_state)
        # Keep only last 10 undo states
        if len(self.data["undo_stack"]) > 10:
            self.data["undo_stack"].pop(0)

    def undo_last_action(self):
        """Undo the last tally action"""
        if self.data["undo_stack"]:
            last_state = self.data["undo_stack"].pop()
            self.data["tallies"] = last_state["tallies"]
            self.data["first_tally_time"] = last_state["first_tally_time"]
            self.data["last_tally_time"] = last_state["last_tally_time"]

            # Update all counter labels
            for counter_name in self.data["settings"]["counters"]:
                if counter_name in self.counter_labels:
                    self.counter_labels[counter_name].config(
                        text=f"{counter_name}: {self.data['tallies'][counter_name]}"
                    )
            self.update_statistics()
            self.play_sound()
        else:
            messagebox.showinfo("Undo", "No actions to undo!")

    def update_statistics(self):
        """Update the statistics display"""
        total = sum(self.data["tallies"].values())
        first_time = self.data.get("first_tally_time")
        last_time = self.data.get("last_tally_time")

        if first_time and last_time:
            first_dt = datetime.fromisoformat(first_time)
            last_dt = datetime.fromisoformat(last_time)
            elapsed = (last_dt - first_dt).total_seconds()

            if elapsed > 0:
                rate_per_min = (total / elapsed) * 60
                stats_text = f"Total: {total} | Elapsed: {int(elapsed//60)}m {int(elapsed%60)}s | Rate: {rate_per_min:.1f}/min"
            else:
                stats_text = f"Total: {total}"
        else:
            stats_text = f"Total: {total}"

        self.stats_label.config(text=stats_text)

    def export_to_csv(self):
        """Export history to CSV file"""
        if not self.data["history"]:
            messagebox.showinfo("Export", "No history to export!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"tally_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    # Get all unique counter names from history
                    all_counters = set()
                    for entry in self.data["history"]:
                        if isinstance(entry, dict) and "tallies" in entry:
                            all_counters.update(entry["tallies"].keys())

                    fieldnames = ["Start Time", "End Time"] + sorted(list(all_counters))
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

                    for entry in self.data["history"]:
                        if isinstance(entry, dict) and "tallies" in entry:
                            row = {}
                            first_time = entry.get("first_tally_time", "")
                            last_time = entry.get("last_tally_time", "")

                            if first_time:
                                row["Start Time"] = datetime.fromisoformat(first_time).strftime("%Y-%m-%d %I:%M%p")
                            else:
                                row["Start Time"] = ""

                            if last_time:
                                row["End Time"] = datetime.fromisoformat(last_time).strftime("%Y-%m-%d %I:%M%p")
                            else:
                                row["End Time"] = ""

                            for counter in all_counters:
                                row[counter] = entry["tallies"].get(counter, 0)

                            writer.writerow(row)

                messagebox.showinfo("Export", f"History exported successfully to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def reset_counter(self, counter_name):
        """Reset an individual counter to zero"""
        if messagebox.askyesno("Reset Counter", f"Reset {counter_name} to 0?"):
            self.save_undo_state()
            self.data["tallies"][counter_name] = 0
            self.counter_labels[counter_name].config(
                text=f"{counter_name}: {self.data['tallies'][counter_name]}"
            )
            self.update_statistics()
            self.play_sound()

    def apply_theme(self):
        """Apply the selected theme to all widgets"""
        theme_name = self.data["settings"].get("theme", "light")
        theme = self.themes.get(theme_name, self.themes["light"])

        self.root.configure(bg=theme["bg"])

        # Apply theme to all widgets recursively
        def apply_to_widget(widget):
            try:
                widget_type = widget.winfo_class()
                if widget_type in ["Frame", "Label"]:
                    widget.configure(bg=theme["bg"], fg=theme["fg"])
                elif widget_type == "Text":
                    widget.configure(bg=theme["text_bg"], fg=theme["fg"])
                elif widget_type == "Button":
                    # Keep the special button colors (green/red) but adjust for theme
                    current_bg = str(widget.cget("bg"))
                    if "green" not in current_bg and "coral" not in current_bg and "red" not in current_bg:
                        widget.configure(bg=theme["button_bg"], fg=theme["fg"])
            except:
                pass

            for child in widget.winfo_children():
                apply_to_widget(child)

        apply_to_widget(self.root)

    def add_tally(self, counter_name):
        self.save_undo_state()
        self.data["tallies"][counter_name] += 1

        # Track timestamps
        current_time = datetime.now().isoformat()
        if self.data["first_tally_time"] is None:
            self.data["first_tally_time"] = current_time
        self.data["last_tally_time"] = current_time

        self.counter_labels[counter_name].config(
            text=f"{counter_name}: {self.data['tallies'][counter_name]}"
        )
        self.update_statistics()
        self.play_sound()

    def subtract_tally(self, counter_name):
        # Only subtract if the count is greater than 0
        if self.data["tallies"][counter_name] > 0:
            self.save_undo_state()
            self.data["tallies"][counter_name] -= 1

            # Update last tally time
            self.data["last_tally_time"] = datetime.now().isoformat()

            self.counter_labels[counter_name].config(
                text=f"{counter_name}: {self.data['tallies'][counter_name]}"
            )
            self.update_statistics()
            self.play_sound()

    def confirm_clear(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the tallies?"):
            self.clear_tallies()

    def clear_tallies(self):
        # Store the current values before clearing
        current_tallies = {name: self.data["tallies"][name]
                          for name in self.data["settings"]["counters"]}

        # Create history entry with timestamps
        history_entry = {
            "tallies": current_tallies,
            "first_tally_time": self.data.get("first_tally_time"),
            "last_tally_time": self.data.get("last_tally_time")
        }

        # Add the current tallies to the history
        self.data["history"].append(history_entry)

        # Limit the history to the configured max_history
        max_history = self.data["settings"]["max_history"]
        if len(self.data["history"]) > max_history:
            self.data["history"] = self.data["history"][-max_history:]

        # Reset all tallies to 0
        for counter_name in self.data["settings"]["counters"]:
            self.data["tallies"][counter_name] = 0
            self.counter_labels[counter_name].config(
                text=f"{counter_name}: {self.data['tallies'][counter_name]}"
            )

        # Reset timestamps
        self.data["first_tally_time"] = None
        self.data["last_tally_time"] = None

        # Update the history display
        self.update_history_display()

    def open_settings(self):
        dialog = SettingsDialog(self.root, self.data["settings"])
        result = dialog.show()

        if result is not None:
            # Preserve existing tally values for counters that still exist
            old_tallies = self.data["tallies"].copy()

            # Update all settings
            self.data["settings"]["counters"] = result["counters"]
            self.data["settings"]["max_history"] = result["max_history"]
            self.data["settings"]["theme"] = result["theme"]
            self.data["settings"]["sound_enabled"] = result["sound_enabled"]

            # Update tallies - keep old values or set to 0
            new_tallies = {}
            for counter in result["counters"]:
                new_tallies[counter] = old_tallies.get(counter, 0)

            self.data["tallies"] = new_tallies

            # Trim history if max_history was reduced
            max_history = result["max_history"]
            if len(self.data["history"]) > max_history:
                self.data["history"] = self.data["history"][-max_history:]

            # Rebuild the UI with new counters and apply theme
            self.build_ui()
            self.apply_theme()

    def toggle_history(self):
        if self.history_text.winfo_viewable():  # Check if the history text is currently visible
            self.history_text.grid_remove()  # Hide it
        else:
            self.history_text.grid()  # Show it
            self.update_history_display()  # Refresh the history display

    def update_history_display(self):
        self.history_text.config(state='normal')  # Enable editing to update the text
        self.history_text.delete(1.0, tk.END)  # Clear the existing text

        for entry in self.data["history"]:
            # Handle new format with timestamps
            if isinstance(entry, dict) and "tallies" in entry:
                # Format tallies
                tallies = entry["tallies"]
                tally_str = ", ".join([f"{k}: {v}" for k, v in tallies.items()])

                # Format dates
                first_time = entry.get("first_tally_time")
                last_time = entry.get("last_tally_time")

                if first_time and last_time:
                    first_dt = datetime.fromisoformat(first_time)
                    last_dt = datetime.fromisoformat(last_time)

                    # Format as date and time
                    first_str = first_dt.strftime("%m/%d/%y %I:%M%p")
                    last_str = last_dt.strftime("%m/%d/%y %I:%M%p")

                    self.history_text.insert(tk.END, f"{tally_str}\n")
                    self.history_text.insert(tk.END, f"  {first_str} - {last_str}\n")
                else:
                    self.history_text.insert(tk.END, f"{tally_str}\n")
                    self.history_text.insert(tk.END, f"  No timestamp data\n")

                self.history_text.insert(tk.END, "\n")
            # Handle old format without timestamp structure
            elif isinstance(entry, dict):
                line = ", ".join([f"{k}: {v}" for k, v in entry.items()])
                self.history_text.insert(tk.END, f"{line}\n")
                self.history_text.insert(tk.END, f"  No timestamp data\n\n")
            elif isinstance(entry, (list, tuple)):
                # Old format compatibility (tuple)
                self.history_text.insert(tk.END, f"Reference: {entry[0]}, Direction: {entry[1]}\n")
                self.history_text.insert(tk.END, f"  No timestamp data\n\n")

        self.history_text.config(state='disabled')  # Disable editing again

    def save_and_quit(self):
        save_tallies(self.data)
        self.root.quit()

    def on_closing(self):
        # Save window position
        geometry = self.root.geometry()
        # Parse geometry string like "450x550+1000+500"
        parts = geometry.split('+')
        if len(parts) == 3:
            self.data["settings"]["window_x"] = int(parts[1])
            self.data["settings"]["window_y"] = int(parts[2])

        # Auto-save when window is closed
        save_tallies(self.data)
        self.root.destroy()

# Set up and run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = TallyApp(root)
    root.mainloop()
