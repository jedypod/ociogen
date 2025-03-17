#!/usr/bin/env python3
import os
import sys
import shutil
import PyOpenColorIO as ocio
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import contextlib
import io

from utilities import colorspaces
from utilities.ocio_utility_functions import create_ocio_colorspace, unbloat


# Make sure we have a recent enough python version
MIN_PYTHON = (3, 7)
if sys.version_info < MIN_PYTHON:
    sys.exit("Python %s.%s or later is required.\n" % MIN_PYTHON)


class OCIOConfigGeneratorGUI:
    def __init__(self, master):
        
        self.master = master
        master.title("OCIO Config Generator")

        self.ocio_version = tk.IntVar(value=2)  # Store OCIO version
        # self.colorspaces_list = self.get_colorspaces()  # Get colorspaces based on OCIO version
        self.colorspaces_list = colorspaces.get_colorspaces(OCIOv=self.ocio_version.get())
        
        self.colorspace_names = [c.name for c in self.colorspaces_list]
        self.colorspaces_names_lin = [c.name for c in self.colorspaces_list if c.encoding == 'scene-linear']
        self.colorspaces_names_log = [c.name for c in self.colorspaces_list if c.encoding == 'log']

        # self.colorspaces = {c.name: c for c in self.colorspaces_list}
        # self.colorspaces_lin = {c.name: c for c in self.colorspaces_list if c.encoding == 'scene-linear'}
        # self.colorspaces_log = {c.name: c for c in self.colorspaces_list if c.encoding == 'log'}

        # --- Variables ---
        self.config_name = tk.StringVar(value="my_config")
        self.output_dir = tk.StringVar(value=os.getcwd())
        self.reference_colorspace = tk.StringVar(value="DaVinci - WideGamut - Linear")
        self.reference_log_colorspace = tk.StringVar(value="DaVinci - WideGamut - Intermediate Log")
        self.lut_size = tk.IntVar(value=2**15)
        self.output_text = tk.StringVar()

        # --- Frames ---
        self.config_frame = ttk.LabelFrame(master, text="Config Settings")
        self.config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.colorspace_frame = ttk.LabelFrame(master, text="Colorspaces")
        self.colorspace_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.reference_frame = ttk.LabelFrame(master, text="Reference Colorspaces")
        self.reference_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # --- Config Settings ---
        ttk.Label(self.config_frame, text="Config Name:").grid(row=0, column=0, sticky="w")
        ttk.Entry(self.config_frame, textvariable=self.config_name).grid(row=0, column=1, sticky="ew")

        ttk.Label(self.config_frame, text="Output Directory:").grid(row=1, column=0, sticky="w")
        ttk.Entry(self.config_frame, textvariable=self.output_dir).grid(row=1, column=1, sticky="ew")
        ttk.Button(self.config_frame, text="Browse", command=self.browse_directory).grid(row=1, column=2, sticky="w")

        ttk.Label(self.config_frame, text="OCIO Major Version:").grid(row=2, column=0, sticky="w")
        # exportselection must be false in order preserve the selection while changing other widgets
        # https://stackoverflow.com/questions/10048609/how-to-keep-selections-highlighted-in-a-tkinter-listbox
        version_combo = ttk.Combobox(self.config_frame, textvariable=self.ocio_version, values=[1, 2], state="readonly", exportselection=False)
        version_combo.grid(row=2, column=1, sticky="ew")
        version_combo.bind("<<ComboboxSelected>>", self.update_colorspaces)  # Bind to event

        # --- Colorspace Selection ---
        self.colorspace_listbox = tk.Listbox(self.colorspace_frame, selectmode=tk.EXTENDED, width=50, height=10, exportselection=False)
        self.update_colorspace_listbox()  # Populate listbox initially
        self.colorspace_listbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.colorspace_scrollbar = ttk.Scrollbar(self.colorspace_frame, orient=tk.VERTICAL, command=self.colorspace_listbox.yview)
        self.colorspace_scrollbar.grid(row=0, column=1, sticky="ns")
        self.colorspace_listbox.config(yscrollcommand=self.colorspace_scrollbar.set)

        # Bind Ctrl+A to select all
        self.colorspace_listbox.bind("<Control-a>", self.select_all_colorspaces)

        self.update_colorspaces()
        # Select all colorspaces by default
        self.select_all_colorspaces(None)

        # --- Reference Colorspaces ---
        ttk.Label(self.reference_frame, text="Reference Colorspace:").grid(row=0, column=0, sticky="w")
        self.reference_combo = ttk.Combobox(self.reference_frame, textvariable=self.reference_colorspace, values=self.colorspaces_names_lin, state="readonly", exportselection=False)
        self.reference_combo.grid(row=0, column=1, sticky="ew")

        ttk.Label(self.reference_frame, text="Reference Log Colorspace:").grid(row=1, column=0, sticky="w")
        self.log_reference_combo = ttk.Combobox(self.reference_frame, textvariable=self.reference_log_colorspace, values=self.colorspaces_names_log, state="readonly", exportselection=False)
        self.log_reference_combo.grid(row=1, column=1, sticky="ew")

        ttk.Label(self.config_frame, text="LUT Size:").grid(row=3, column=0, sticky="w")
        ttk.Entry(self.config_frame, textvariable=self.lut_size).grid(row=3, column=1, sticky="ew")

        # --- Generate Button ---
        generate_button = ttk.Button(master, text="Generate Config", command=self.generate_config)
        generate_button.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        
        # --- Output Text Box ---
        # Disabled initially, enable when writing
        self.output_display = tk.Text(master, height=30, state='disabled')
        self.output_display.grid(row=20, column=0, padx=10, pady=5, sticky="ew")
        


        # --- Configure Grid Weights ---
        master.columnconfigure(0, weight=1)
        self.config_frame.columnconfigure(1, weight=1)
        self.colorspace_frame.columnconfigure(0, weight=1)
        self.reference_frame.columnconfigure(1, weight=1)
        

    def get_colorspaces(self):
        return colorspaces.get_colorspaces(OCIOv=self.ocio_version.get())

    def update_colorspaces(self, event=None):
        # Store current selection (names) before updating
        selected_names = [self.colorspace_listbox.get(i) for i in self.colorspace_listbox.curselection()]

        self.colorspaces_list = self.get_colorspaces()
        self.colorspace_names = [c.name for c in self.colorspaces_list]
        self.colorspaces_names_lin = [c.name for c in self.colorspaces_list if c.encoding == 'scene-linear']
        self.colorspaces_names_log = [c.name for c in self.colorspaces_list if c.encoding == 'log']


    def update_colorspace_listbox(self):
        self.colorspace_listbox.delete(0, tk.END)
        for name in self.colorspace_names:
            self.colorspace_listbox.insert(tk.END, name)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)

    def generate_config(self):
        # Clear output text box
        self.clear_output_text()

        # Redirect output to text box
        with self.redirect_stdout() as output_string:
            try:
                ocio_version_major = self.ocio_version.get()
                LUT_SIZE = self.lut_size.get()
                # Get selected colorspaces
                all_colorspaces = colorspaces.get_colorspaces(OCIOv=ocio_version_major)

                selected_colorspace_names = [self.colorspace_listbox.get(i) for i in self.colorspace_listbox.curselection()]
                all_colorspace_names = [c.name for c in all_colorspaces]
                selected_colorspaces = []
                
                
                reference_colorspace = None
                reference_log_colorspace = None
                for c in all_colorspaces:
                    if c.name in selected_colorspace_names:
                        selected_colorspaces.append(c)
                    if c.name == self.reference_colorspace.get():
                        reference_colorspace = c
                    if c.name == self.reference_log_colorspace.get():
                        reference_log_colorspace = c
                # print(f'Selected Colorspaces! {selected_colorspaces}')

                config = ocio.Config()
                config.setMajorVersion(ocio_version_major)
                config.setMinorVersion(0) # always 0 for now
                config.setSearchPath('luts')
                
                config_dir = os.path.join(self.output_dir.get(), f'{self.config_name.get()}')
                if os.path.exists(config_dir):
                    shutil.rmtree(config_dir)
                if not os.path.isdir(config_dir):
                    os.makedirs(config_dir)
                config_path = os.path.join(config_dir, 'config.ocio')
                

                # config.setRole('aces_interchange', "ACES 2065-1")
                config.setRole('scene_linear', reference_colorspace.name)
                config.setRole('reference', reference_colorspace.name)
                config.setRole('color_timing', reference_log_colorspace.name)
                config.setRole('compositing_log', reference_log_colorspace.name)
                config.setRole('data', reference_colorspace.name)
                config.setRole('default', reference_colorspace.name)
                config.setRole('color_picking', reference_colorspace.name)
                config.setRole('mattepaint', reference_log_colorspace.name)
                config.setRole('texture_paint', reference_colorspace.name)
                
                # Add Colorspaces
                for c in selected_colorspaces:
                    cs = create_ocio_colorspace(c, reference_colorspace, ocio_version_major, config_dir, LUT_SIZE=LUT_SIZE)
                    config.addColorSpace(cs)
                
                # Set Displays
                config.addDisplayView(display="Rec1886", view='Display Encoding', colorSpaceName='Display Encoding - Rec1886')
                config.addDisplayView(display="Rec1886", view='Bypass', colorSpaceName=f'{reference_colorspace.name}')
                
                config.setActiveDisplays("Rec1886")
                config.setActiveViews(', '.join(['Display Encoding', 'Bypass']))
                config.validate()
                
                cfg = config.serialize()
                cfg = unbloat(cfg)
                with open(config_path, 'w') as f:
                    f.write(cfg)
            
                
                self.print_output_text("Config generated successfully!\n")


            except Exception as e:
                import traceback
                error_message = traceback.format_exc() # Get full traceback
                self.print_output_text(f"Error during config generation:\n{error_message}\n")

        # Display captured output
        self.print_output_text(output_string.getvalue())


    @contextlib.contextmanager
    def redirect_stdout(self):
        ''' Redirect stdout to a string variable to display in GUI '''
        original_stdout = sys.stdout
        output_buffer = io.StringIO()
        sys.stdout = output_buffer
        try:
            yield output_buffer
        finally:
            sys.stdout = original_stdout


    def print_output_text(self, text):
        ''' Print to the output text box in the GUI '''
        self.output_display.config(state='normal') # Enable text box to write
        self.output_display.insert(tk.END, text)
        self.output_display.config(state='disabled') # Disable again after writing
        self.output_display.see(tk.END) # Scroll to the end

    def clear_output_text(self):
        ''' Clear the output text box '''
        self.output_display.config(state='normal')
        self.output_display.delete(1.0, tk.END) # Delete all text
        self.output_display.config(state='disabled')

    def select_all_colorspaces(self, event=None):
        for i in range(self.colorspace_listbox.size()):
            self.colorspace_listbox.selection_set(i)


if __name__ == "__main__":
    root = tk.Tk()
    gui = OCIOConfigGeneratorGUI(root)
    root.mainloop()