import tkinter as tk
import os
import json
from tkinter import messagebox  # Import messagebox for confirmation

# File to save tallies
TALLY_FILE = "tallies.json"

# Load tallies from file
def load_tallies():
    if os.path.exists(TALLY_FILE):
        with open(TALLY_FILE, "r") as file:
            tallies = json.load(file)
            # Ensure the history key exists
            if "history" not in tallies:
                tallies["history"] = []
            return tallies
    return {"Reference": 0, "Direction": 0, "history": []}  # Default tallies and history

# Save tallies to file
def save_tallies(tallies):
    with open(TALLY_FILE, "w") as file:
        json.dump(tallies, file)

class TallyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tally Counter")
        self.root.geometry("250x200+1000+500")  # Adjusted size and position
        self.root.attributes("-topmost", True)  # Always on top

        self.tallies = load_tallies()

        # Button to toggle history display
        self.toggle_history_btn = tk.Button(root, text="Toggle History", command=self.toggle_history)
        self.toggle_history_btn.grid(row=0, column=0, sticky='ew')

        # History text area
        self.history_text = tk.Text(root, height=4, width=25, state='disabled')  # Text area for history
        self.history_text.grid(row=1, column=0, sticky='ew')
        self.history_text.grid_remove()  # Initially hidden

        self.label1 = tk.Label(root, text="Reference: " + str(self.tallies["Reference"]))
        self.label1.grid(row=2, column=0)

        self.label2 = tk.Label(root, text="Direction: " + str(self.tallies["Direction"]))
        self.label2.grid(row=3, column=0)

        self.btn1 = tk.Button(root, text="Add to Reference", command=self.add_tally1)
        self.btn1.grid(row=4, column=0)

        self.btn2 = tk.Button(root, text="Add to Direction", command=self.add_tally2)
        self.btn2.grid(row=5, column=0)

        # Save & Quit button positioned above Clear button
        self.save_btn = tk.Button(root, text="Save & Quit", command=self.save_and_quit)
        self.save_btn.grid(row=6, column=0, sticky='ew')

        # Clear Tallies button with confirmation
        self.clear_btn = tk.Button(root, text="Clear", command=self.confirm_clear, width=6, height=1, bg="red")
        self.clear_btn.grid(row=7, column=0, sticky='e')  # Position in lower-right corner

        self.update_history_display()  # Display the initial history

    def add_tally1(self):
        self.tallies["Reference"] += 1
        self.label1.config(text="Reference: " + str(self.tallies["Reference"]))

    def add_tally2(self):
        self.tallies["Direction"] += 1
        self.label2.config(text="Direction: " + str(self.tallies["Direction"]))

    def confirm_clear(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the tallies?"):
            self.clear_tallies()

    def clear_tallies(self):
        # Store the current values before clearing
        current_tallies = (self.tallies["Reference"], self.tallies["Direction"])

        # Add the current tallies to the history
        self.tallies["history"].append(current_tallies)

        # Limit the history to the last 2 entries
        if len(self.tallies["history"]) > 2:
            self.tallies["history"].pop(0)

        # Reset tallies to 0
        self.tallies["Reference"] = 0
        self.tallies["Direction"] = 0
        self.label1.config(text="Reference: " + str(self.tallies["Reference"]))
        self.label2.config(text="Direction: " + str(self.tallies["Direction"]))

        # Update the history display
        self.update_history_display()

    def toggle_history(self):
        if self.history_text.winfo_viewable():  # Check if the history text is currently visible
            self.history_text.grid_remove()  # Hide it
        else:
            self.history_text.grid()  # Show it
            self.update_history_display()  # Refresh the history display

    def update_history_display(self):
        self.history_text.config(state='normal')  # Enable editing to update the text
        self.history_text.delete(1.0, tk.END)  # Clear the existing text

        for tally in self.tallies["history"]:
            self.history_text.insert(tk.END, f"Reference: {tally[0]}, Direction: {tally[1]}\n")

        self.history_text.config(state='disabled')  # Disable editing again

    def save_and_quit(self):
        save_tallies(self.tallies)
        self.root.quit()

# Set up and run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = TallyApp(root)
    root.mainloop()
