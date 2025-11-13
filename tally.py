import tkinter as tk
import os
import json
from tkinter import messagebox, simpledialog  # Import messagebox for confirmation

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
                        "counters": list(old_tallies.keys())
                    },
                    "tallies": old_tallies,
                    "history": data.get("history", [])
                }
            # Ensure the history key exists
            if "history" not in data:
                data["history"] = []
            return data
    # Default structure
    return {
        "settings": {
            "counters": ["Reference", "Direction"]
        },
        "tallies": {
            "Reference": 0,
            "Direction": 0
        },
        "history": []
    }

# Save tallies to file
def save_tallies(data):
    with open(TALLY_FILE, "w") as file:
        json.dump(data, file)

# Settings Dialog
class SettingsDialog:
    def __init__(self, parent, current_counters):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("300x400")
        self.dialog.attributes("-topmost", True)

        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        tk.Label(self.dialog, text="Counter Names:", font=('Arial', 10, 'bold')).pack(pady=5)

        # Frame for counter list
        list_frame = tk.Frame(self.dialog)
        list_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        # Scrollbar for listbox
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.counter_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=10)
        self.counter_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.counter_listbox.yview)

        # Populate listbox with current counters
        for counter in current_counters:
            self.counter_listbox.insert(tk.END, counter)

        # Buttons frame
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Add Counter", command=self.add_counter, width=12).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Remove Selected", command=self.remove_counter, width=12).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Rename Selected", command=self.rename_counter, width=12).grid(row=1, column=0, columnspan=2, pady=5)

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

    def save(self):
        counters = list(self.counter_listbox.get(0, tk.END))
        if not counters:
            messagebox.showwarning("Warning", "You must have at least one counter!", parent=self.dialog)
            return
        self.result = counters
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
        self.root.geometry("300x400+1000+500")  # Adjusted size
        self.root.attributes("-topmost", True)  # Always on top

        self.data = load_tallies()

        # Storage for dynamic widgets
        self.counter_labels = {}
        self.counter_buttons = {}

        self.build_ui()

    def build_ui(self):
        # Clear existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        self.counter_labels.clear()
        self.counter_buttons.clear()

        current_row = 0

        # Settings button
        settings_btn = tk.Button(self.root, text="Settings", command=self.open_settings)
        settings_btn.grid(row=current_row, column=0, sticky='ew', padx=5, pady=2)
        current_row += 1

        # Button to toggle history display
        self.toggle_history_btn = tk.Button(self.root, text="Toggle History", command=self.toggle_history)
        self.toggle_history_btn.grid(row=current_row, column=0, sticky='ew', padx=5, pady=2)
        current_row += 1

        # History text area
        self.history_text = tk.Text(self.root, height=4, width=30, state='disabled')
        self.history_text.grid(row=current_row, column=0, sticky='ew', padx=5, pady=2)
        self.history_text.grid_remove()  # Initially hidden
        current_row += 1

        # Dynamically create counters based on settings
        counters = self.data["settings"]["counters"]

        # Ensure all counters exist in tallies
        for counter in counters:
            if counter not in self.data["tallies"]:
                self.data["tallies"][counter] = 0

        for counter_name in counters:
            # Label showing current count
            label = tk.Label(self.root, text=f"{counter_name}: {self.data['tallies'][counter_name]}")
            label.grid(row=current_row, column=0, padx=5, pady=2)
            self.counter_labels[counter_name] = label
            current_row += 1

            # Button to increment
            btn = tk.Button(self.root, text=f"Add to {counter_name}",
                          command=lambda name=counter_name: self.add_tally(name))
            btn.grid(row=current_row, column=0, sticky='ew', padx=5, pady=2)
            self.counter_buttons[counter_name] = btn
            current_row += 1

        # Save & Quit button
        self.save_btn = tk.Button(self.root, text="Save & Quit", command=self.save_and_quit)
        self.save_btn.grid(row=current_row, column=0, sticky='ew', padx=5, pady=5)
        current_row += 1

        # Clear Tallies button with confirmation
        self.clear_btn = tk.Button(self.root, text="Clear", command=self.confirm_clear,
                                   width=6, height=1, bg="red")
        self.clear_btn.grid(row=current_row, column=0, sticky='e', padx=5, pady=2)

        self.update_history_display()

    def add_tally(self, counter_name):
        self.data["tallies"][counter_name] += 1
        self.counter_labels[counter_name].config(
            text=f"{counter_name}: {self.data['tallies'][counter_name]}"
        )

    def confirm_clear(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the tallies?"):
            self.clear_tallies()

    def clear_tallies(self):
        # Store the current values before clearing
        current_tallies = {name: self.data["tallies"][name]
                          for name in self.data["settings"]["counters"]}

        # Add the current tallies to the history
        self.data["history"].append(current_tallies)

        # Limit the history to the last 2 entries
        if len(self.data["history"]) > 2:
            self.data["history"].pop(0)

        # Reset all tallies to 0
        for counter_name in self.data["settings"]["counters"]:
            self.data["tallies"][counter_name] = 0
            self.counter_labels[counter_name].config(
                text=f"{counter_name}: {self.data['tallies'][counter_name]}"
            )

        # Update the history display
        self.update_history_display()

    def open_settings(self):
        dialog = SettingsDialog(self.root, self.data["settings"]["counters"])
        new_counters = dialog.show()

        if new_counters is not None:
            # Preserve existing tally values for counters that still exist
            old_tallies = self.data["tallies"].copy()

            # Update settings
            self.data["settings"]["counters"] = new_counters

            # Update tallies - keep old values or set to 0
            new_tallies = {}
            for counter in new_counters:
                new_tallies[counter] = old_tallies.get(counter, 0)

            self.data["tallies"] = new_tallies

            # Rebuild the UI with new counters
            self.build_ui()

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
            # Handle both old format (tuples) and new format (dicts)
            if isinstance(entry, dict):
                line = ", ".join([f"{k}: {v}" for k, v in entry.items()])
                self.history_text.insert(tk.END, f"{line}\n")
            elif isinstance(entry, (list, tuple)):
                # Old format compatibility
                self.history_text.insert(tk.END, f"Reference: {entry[0]}, Direction: {entry[1]}\n")

        self.history_text.config(state='disabled')  # Disable editing again

    def save_and_quit(self):
        save_tallies(self.data)
        self.root.quit()

# Set up and run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = TallyApp(root)
    root.mainloop()
