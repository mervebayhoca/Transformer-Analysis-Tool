import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import messagebox
import datetime

# --- SETTINGS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TransformerProApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Main Window
        self.title("Transformer Analysis Tool (Pro Edition)")
        self.geometry("1100x700")
        self.resizable(True, True)

        # --- LAYOUT CONFIGURATION ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT SIDEBAR (INPUTS) ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.lbl_title = ctk.CTkLabel(self.sidebar, text="⚡ Control Panel", font=("Arial", 20, "bold"))
        self.lbl_title.pack(pady=20)

        # Mode Switch
        self.mode_var = ctk.StringVar(value="Standard")
        self.switch = ctk.CTkSwitch(self.sidebar, text="Lab Mode (Test Data)", command=self.toggle_mode,
                                    variable=self.mode_var, onvalue="Lab", offvalue="Standard")
        self.switch.pack(pady=10)

        # Common Inputs
        self.frame_inputs = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_inputs.pack(fill="x", padx=10)
        
        self.entry_sn = self.add_input(self.frame_inputs, "Rated Power (Sn) [VA]:", "20000")
        self.entry_v1 = self.add_input(self.frame_inputs, "Primary Voltage (V1) [V]:", "2000")
        
        ctk.CTkLabel(self.frame_inputs, text="Power Factor (PF):").pack(anchor="w", padx=10, pady=(10,0))
        self.slider_pf = ctk.CTkSlider(self.frame_inputs, from_=0.1, to=1.0, number_of_steps=90, command=self.run_analysis)
        self.slider_pf.set(0.8)
        self.slider_pf.pack(fill="x", padx=10)

        # Dynamic Inputs Area
        self.frame_dynamic = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.frame_dynamic.pack(fill="x", padx=10, pady=10)
        
        # Define Input fields (Hidden initially)
        self.inp_p_core = ctk.CTkEntry(self.frame_dynamic) # Standard
        self.inp_p_cu = ctk.CTkEntry(self.frame_dynamic)   # Standard
        self.inp_vsc = ctk.CTkEntry(self.frame_dynamic)    # Lab
        self.inp_isc = ctk.CTkEntry(self.frame_dynamic)    # Lab
        self.inp_psc = ctk.CTkEntry(self.frame_dynamic)    # Lab

        self.setup_standard_ui() # Default View

        # Run Button
        self.btn_run = ctk.CTkButton(self.sidebar, text="RUN ANALYSIS", command=self.run_analysis, height=40, font=("Arial", 14, "bold"))
        self.btn_run.pack(padx=20, pady=20, fill="x")

        # Save Button
        self.btn_save = ctk.CTkButton(self.sidebar, text="💾 Save Report", command=self.save_report, fg_color="green", hover_color="darkgreen")
        self.btn_save.pack(padx=20, fill="x")

        # --- RIGHT SIDE (TABS) ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.tab_eff = self.tabview.add("Efficiency")
        self.tab_reg = self.tabview.add("Regulation")
        self.tab_data = self.tabview.add("Parameters")

        # Plots
        self.fig_eff, self.ax_eff = plt.subplots(figsize=(5,4), dpi=100)
        self.canvas_eff = FigureCanvasTkAgg(self.fig_eff, master=self.tab_eff)
        self.canvas_eff.get_tk_widget().pack(fill="both", expand=True)

        self.fig_reg, self.ax_reg = plt.subplots(figsize=(5,4), dpi=100)
        self.canvas_reg = FigureCanvasTkAgg(self.fig_reg, master=self.tab_reg)
        self.canvas_reg.get_tk_widget().pack(fill="both", expand=True)

        # Results Label
        self.lbl_res = ctk.CTkLabel(self.tab_data, text="Run analysis...", font=("Courier", 14), justify="left")
        self.lbl_res.pack(padx=20, pady=20, anchor="nw")

        # Initial Calculation
        self.run_analysis(None)

    def add_input(self, parent, text, default):
        ctk.CTkLabel(parent, text=text, anchor="w").pack(fill="x", pady=(5,0))
        entry = ctk.CTkEntry(parent)
        entry.insert(0, default)
        entry.pack(fill="x")
        return entry

    def toggle_mode(self):
        for widget in self.frame_dynamic.winfo_children(): widget.pack_forget()
        if self.mode_var.get() == "Standard": self.setup_standard_ui()
        else: self.setup_lab_ui()

    def setup_standard_ui(self):
        ctk.CTkLabel(self.frame_dynamic, text="Core Loss [W]:", anchor="w").pack(fill="x")
        self.inp_p_core.pack(fill="x"); self.inp_p_core.delete(0,'end'); self.inp_p_core.insert(0,"150")
        ctk.CTkLabel(self.frame_dynamic, text="Copper Loss [W]:", anchor="w").pack(fill="x")
        self.inp_p_cu.pack(fill="x"); self.inp_p_cu.delete(0,'end'); self.inp_p_cu.insert(0,"300")

    def setup_lab_ui(self):
        ctk.CTkLabel(self.frame_dynamic, text="Test Vsc [V]:", anchor="w").pack(fill="x")
        self.inp_vsc.pack(fill="x"); self.inp_vsc.delete(0,'end'); self.inp_vsc.insert(0,"40")
        ctk.CTkLabel(self.frame_dynamic, text="Test Isc [A]:", anchor="w").pack(fill="x")
        self.inp_isc.pack(fill="x"); self.inp_isc.delete(0,'end'); self.inp_isc.insert(0,"10")
        ctk.CTkLabel(self.frame_dynamic, text="Test Psc [W]:", anchor="w").pack(fill="x")
        self.inp_psc.pack(fill="x"); self.inp_psc.delete(0,'end'); self.inp_psc.insert(0,"300")

    def run_analysis(self, _):
        try:
            Sn = float(self.entry_sn.get())
            V1 = float(self.entry_v1.get())
            pf = self.slider_pf.get()

            # Logic
            if self.mode_var.get() == "Standard":
                P_core = float(self.inp_p_core.get())
                P_cu = float(self.inp_p_cu.get())
                R_eq = P_cu / ((Sn/V1)**2)
                X_eq = R_eq * 3
            else:
                Vsc = float(self.inp_vsc.get())
                Isc = float(self.inp_isc.get())
                Psc = float(self.inp_psc.get())
                P_core = 150 # Fixed
                P_cu = Psc
                R_eq = Psc / (Isc**2)
                Z_eq = Vsc / Isc
                X_eq = np.sqrt(Z_eq**2 - R_eq**2)

            # Calculate Curves
            x = np.linspace(0.01, 1.25, 100)
            P_out = x * Sn * pf
            eff = (P_out / (P_out + P_core + x**2 * P_cu)) * 100
            
            sin_phi = np.sqrt(1 - pf**2)
            reg = x * ( (R_eq*Sn/V1**2)*pf + (X_eq*Sn/V1**2)*sin_phi ) * 100

            # Plot Efficiency
            self.ax_eff.clear()
            self.ax_eff.plot(x*100, eff, '#00E5FF', lw=2)
            self.ax_eff.set_title(f"Efficiency (Max: {np.max(eff):.2f}%)")
            self.ax_eff.grid(True, alpha=0.3)
            self.canvas_eff.draw()

            # Plot Regulation
            self.ax_reg.clear()
            self.ax_reg.plot(x*100, reg, '#FF5252', lw=2)
            self.ax_reg.set_title("Voltage Regulation %")
            self.ax_reg.grid(True, alpha=0.3)
            self.canvas_reg.draw()

            # Update Text
            self.lbl_res.configure(text=f"RESULTS:\nMax Eff: {np.max(eff):.2f}%\nR_eq: {R_eq:.4f} Ohm\nX_eq: {X_eq:.4f} Ohm")

        except ValueError: pass

    def save_report(self):
        with open(f"Report_{datetime.datetime.now().strftime('%H%M%S')}.txt", "w") as f:
            f.write(self.lbl_res.cget("text"))
        messagebox.showinfo("Saved", "Report saved successfully!")

if __name__ == "__main__":
    app = TransformerProApp()
    app.mainloop()
