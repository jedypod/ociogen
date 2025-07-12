import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import re
import yaml
import contextlib
import io
import shutil
import PyOpenColorIO as ocio
import importlib.resources # Added for package data access
from collections import OrderedDict # For ordered roles
from dataclasses import asdict
import tkinter.font as tkFont
from tkinter import simpledialog

from .core import OCIOConfig, Colorspace, VALID_LUT_EXTENSIONS


# --- Dark Theme Configuration ---
DARK_BG = "#2E2E2E"
DARK_FG = "#E0E0E0"
DARK_WIDGET_BG = "#3C3C3C"
DARK_SELECT_BG = "#555555"
DARK_SELECT_FG = "#FFFFFF"
DARK_INSERT_BG = "#FFFFFF" # Cursor color
DARK_BUTTON_BG = "#4A4A4A"
DARK_BUTTON_FG = DARK_FG
DARK_BUTTON_ACTIVE_BG = "#5A5A5A"
DARK_ERROR_FG = "#FF6B6B"
DARK_MANUAL_FG = "#6B9AFF"
DARK_DISABLED_FG = "#777777"
DARK_OUTLINE = "#666666" # Color for outlines/borders/focus


# --- Light Theme Configuration (Cross-Platform Safe) ---
LIGHT_BG = '#F0F0F0' # Standard light gray
LIGHT_FG = '#000000' # Black
LIGHT_WIDGET_BG = '#FFFFFF' # White
LIGHT_SELECT_BG = '#B2D7FF' # Light blue
LIGHT_SELECT_FG = '#000000' # Black
LIGHT_INSERT_BG = '#000000' # Black cursor
LIGHT_BUTTON_BG = '#F0F0F0' # Same as main background
LIGHT_BUTTON_FG = '#000000' # Black
LIGHT_BUTTON_ACTIVE_BG = '#E5F1FB' # Very light blue
LIGHT_DISABLED_FG = '#A0A0A0' # Gray
LIGHT_OUTLINE = '#A0A0A0' # Gray outline/border
LIGHT_SCROLL_TROUGH = '#E0E0E0' # Slightly darker gray for scrollbar trough



def apply_dark_theme(root):
    """Configures ttk styles and root options for a dark theme."""
    root.configure(bg=DARK_BG)
    style = ttk.Style(root)
    # Use 'clam' theme as it's generally more customizable
    # Available themes can be checked with style.theme_names()
    # Fallback if 'clam' is not available (though it usually is on major platforms)
    # Apply clam theme only on Windows, as it fixes background issues there,
    # but causes outline issues elsewhere that are hard to suppress.
    # Keep default theme on Linux/macOS.
    if sys.platform == 'win32':
        try:
            style.theme_use('clam')
        except tk.TclError:
            print("Warning: 'clam' theme not found on Windows, using default.")

    # --- Configure ttk Styles ---
    # General settings for all ttk widgets
    style.configure('.',
                    background=DARK_BG,
                    foreground=DARK_FG,
                    fieldbackground=DARK_WIDGET_BG,
                    borderwidth=1,
                    focuscolor=DARK_BG) # Make focus highlight match background
    style.map('.',
              background=[('active', DARK_BUTTON_ACTIVE_BG), ('disabled', DARK_BG)],
              foreground=[('disabled', DARK_DISABLED_FG)])

    # Specific widget styling
    style.configure('TFrame', background=DARK_BG, borderwidth=0, highlightthickness=0, relief=tk.FLAT) # Ensure flat relief
    style.configure('TLabel', background=DARK_BG, foreground=DARK_FG)
    # Explicitly set borderwidth/highlightthickness to 0 for Button, add bordercolor
    style.configure('TButton', background=DARK_BUTTON_BG, foreground=DARK_BUTTON_FG, borderwidth=0, relief=tk.FLAT, highlightthickness=0, bordercolor=DARK_BG)
    style.map('TButton', background=[('active', DARK_BUTTON_ACTIVE_BG), ('pressed', DARK_BUTTON_ACTIVE_BG)]) # Keep visual feedback on press
    # Explicitly set borderwidth/highlightthickness to 0 for Entry, add bordercolor and flat relief
    style.configure('TEntry', insertcolor=DARK_INSERT_BG, fieldbackground=DARK_WIDGET_BG, foreground=DARK_FG, borderwidth=0, highlightthickness=0, bordercolor=DARK_BG, relief=tk.FLAT)
    style.configure('TCheckbutton', background=DARK_BG, foreground=DARK_FG)
    style.map('TCheckbutton',
              #   indicatorcolor=[('selected', DARK_SELECT_BG), ('!selected', DARK_WIDGET_BG)],
              indicatorcolor=[('selected', DARK_SELECT_FG), ('!selected', DARK_WIDGET_BG)], # Brighter indicator when selected
              background=[('active', DARK_BG)],
              foreground=[('active', DARK_FG), ('disabled', DARK_DISABLED_FG)]) # Add disabled foreground color
    style.configure('TRadiobutton', background=DARK_BG, foreground=DARK_FG)
    style.map('TRadiobutton',
              indicatorcolor=[('selected', DARK_SELECT_FG), ('!selected', DARK_WIDGET_BG)], # Brighter indicator when selected
              background=[('active', DARK_BG)],
              foreground=[('active', DARK_FG)])

    # Combobox styling (dropdown list styling is OS-dependent)
    # Explicitly set borderwidth/highlightthickness to 0 for Combobox, add bordercolor and flat relief
    style.configure('TCombobox', fieldbackground=DARK_WIDGET_BG, background=DARK_BUTTON_BG, foreground=DARK_FG, insertcolor=DARK_INSERT_BG, arrowcolor=DARK_FG, borderwidth=0, highlightthickness=0, bordercolor=DARK_BG, relief=tk.FLAT)
    style.map('TCombobox', fieldbackground=[('readonly', DARK_WIDGET_BG)],
                         selectbackground=[('readonly', DARK_SELECT_BG)],
                         selectforeground=[('readonly', DARK_SELECT_FG)],
                         background=[('readonly', DARK_BUTTON_BG)])
    # Attempt to style the dropdown list (may not work consistently across platforms)
    root.option_add('*TCombobox*Listbox.background', DARK_WIDGET_BG)
    root.option_add('*TCombobox*Listbox.foreground', DARK_FG)
    root.option_add('*TCombobox*Listbox.selectBackground', DARK_SELECT_BG)
    root.option_add('*TCombobox*Listbox.selectForeground', DARK_SELECT_FG)

    style.configure('TNotebook', background=DARK_BG, borderwidth=0, highlightthickness=0, relief=tk.FLAT) # Ensure flat relief
    style.configure('TNotebook.Tab', background=DARK_BUTTON_BG, foreground=DARK_FG, padding=[5, 2], borderwidth=0)
    style.map('TNotebook.Tab', background=[('selected', DARK_BG)], foreground=[('selected', DARK_FG)])

    style.configure('Treeview', background=DARK_WIDGET_BG, foreground=DARK_FG, fieldbackground=DARK_WIDGET_BG, rowheight=25)
    style.map('Treeview', background=[('selected', DARK_SELECT_BG)], foreground=[('selected', DARK_SELECT_FG)])
    style.configure('Treeview.Heading', background=DARK_BUTTON_BG, foreground=DARK_BUTTON_FG, relief='flat', borderwidth=0)
    style.map('Treeview.Heading', background=[('active', DARK_BUTTON_ACTIVE_BG)])

    style.configure('Vertical.TScrollbar', background=DARK_BUTTON_BG, troughcolor=DARK_BG, bordercolor=DARK_BG, arrowcolor=DARK_FG)
    style.map('Vertical.TScrollbar', background=[('active', DARK_BUTTON_ACTIVE_BG)])
    style.configure('Horizontal.TScrollbar', background=DARK_BUTTON_BG, troughcolor=DARK_BG, bordercolor=DARK_BG, arrowcolor=DARK_FG)
    style.map('Horizontal.TScrollbar', background=[('active', DARK_BUTTON_ACTIVE_BG)])

    # Explicitly set borderwidth/highlightthickness to 0 for Spinbox, add bordercolor and flat relief
    style.configure('TSpinbox', fieldbackground=DARK_WIDGET_BG, background=DARK_BUTTON_BG, foreground=DARK_FG, arrowcolor=DARK_FG, insertcolor=DARK_INSERT_BG, borderwidth=0, highlightthickness=0, bordercolor=DARK_BG, relief=tk.FLAT)
    style.map('TSpinbox', background=[('active', DARK_BUTTON_ACTIVE_BG)])

    style.configure('TLabelframe', background=DARK_BG, bordercolor=DARK_OUTLINE) # Use darker border
    style.configure('TLabelframe.Label', background=DARK_BG, foreground=DARK_FG)

    # --- Configure tk Widget Options (via root options) ---
    # These provide defaults but might be overridden by specific widget configs
    root.option_add('*background', DARK_BG)
    root.option_add('*foreground', DARK_FG)
    root.option_add('*highlightBackground', DARK_BG) # Border when not focused
    root.option_add('*highlightColor', DARK_BG)      # Border when focused (Tk widgets) - Match background
    root.option_add('*highlightThickness', 0)             # Attempt to remove focus border globally

# --- End Dark Theme Configuration ---

def apply_light_theme(root):
    """Resets ttk styles and root options towards the default light theme."""
    # Use standard hex codes or common names for better cross-platform compatibility.
    LIGHT_BG = '#F0F0F0' # Standard light gray
    LIGHT_FG = '#000000' # Black
    LIGHT_WIDGET_BG = '#FFFFFF' # White
    LIGHT_SELECT_BG = '#B2D7FF' # Light blue
    LIGHT_SELECT_FG = '#000000' # Black
    LIGHT_INSERT_BG = '#000000' # Black cursor
    LIGHT_BUTTON_BG = '#F0F0F0' # Same as main background
    LIGHT_BUTTON_FG = '#000000' # Black
    LIGHT_BUTTON_ACTIVE_BG = '#E5F1FB' # Very light blue
    LIGHT_DISABLED_FG = '#A0A0A0' # Gray
    LIGHT_OUTLINE = '#A0A0A0' # Gray outline/border
    LIGHT_SCROLL_TROUGH = '#E0E0E0' # Slightly darker gray for scrollbar trough

    root.configure(bg=LIGHT_BG)
    style = ttk.Style(root)

    # Reset general ttk styles
    style.configure('.',
                    background=LIGHT_BG,
                    foreground=LIGHT_FG,
                    fieldbackground=LIGHT_WIDGET_BG,
                    borderwidth=1,
                    focuscolor=LIGHT_FG) # Use foreground color for focus
    style.map('.',
              background=[('active', LIGHT_BUTTON_ACTIVE_BG), ('disabled', LIGHT_BG)],
              foreground=[('disabled', LIGHT_DISABLED_FG)])

    # Reset specific widget styling
    style.configure('TFrame', background=LIGHT_BG, borderwidth=0, highlightthickness=0, relief=tk.FLAT)
    style.configure('TLabel', background=LIGHT_BG, foreground=LIGHT_FG)
    style.configure('TButton', background=LIGHT_BUTTON_BG, foreground=LIGHT_BUTTON_FG, borderwidth=1, relief=tk.RAISED, highlightthickness=1, bordercolor=LIGHT_OUTLINE)
    style.map('TButton', background=[('active', LIGHT_BUTTON_ACTIVE_BG), ('pressed', '#C0C0C0')]) # Slightly darker gray pressed
    style.configure('TEntry', insertcolor=LIGHT_INSERT_BG, fieldbackground=LIGHT_WIDGET_BG, foreground=LIGHT_FG, borderwidth=1, highlightthickness=1, bordercolor=LIGHT_OUTLINE, relief=tk.SUNKEN)
    style.configure('TCheckbutton', background=LIGHT_BG, foreground=LIGHT_FG)
    style.map('TCheckbutton',
              indicatorcolor=[('selected', LIGHT_FG), ('!selected', LIGHT_WIDGET_BG)],
              background=[('active', LIGHT_BG)],
              foreground=[('active', LIGHT_FG), ('disabled', LIGHT_DISABLED_FG)])
    style.configure('TRadiobutton', background=LIGHT_BG, foreground=LIGHT_FG)
    style.map('TRadiobutton',
              indicatorcolor=[('selected', LIGHT_FG), ('!selected', LIGHT_WIDGET_BG)],
              background=[('active', LIGHT_BG)],
              foreground=[('active', LIGHT_FG)])

    # Reset Combobox
    style.configure('TCombobox', fieldbackground=LIGHT_WIDGET_BG, background=LIGHT_BUTTON_BG, foreground=LIGHT_FG, insertcolor=LIGHT_INSERT_BG, arrowcolor=LIGHT_FG, borderwidth=1, highlightthickness=1, bordercolor=LIGHT_OUTLINE, relief=tk.SUNKEN)
    style.map('TCombobox', fieldbackground=[('readonly', LIGHT_WIDGET_BG)],
                         selectbackground=[('readonly', LIGHT_SELECT_BG)],
                         selectforeground=[('readonly', LIGHT_SELECT_FG)],
                         background=[('readonly', LIGHT_BUTTON_BG)])
    # Reset Combobox Listbox options
    root.option_add('*TCombobox*Listbox.background', LIGHT_WIDGET_BG)
    root.option_add('*TCombobox*Listbox.foreground', LIGHT_FG)
    root.option_add('*TCombobox*Listbox.selectBackground', LIGHT_SELECT_BG)
    root.option_add('*TCombobox*Listbox.selectForeground', LIGHT_SELECT_FG)

    style.configure('TNotebook', background=LIGHT_BG, borderwidth=1, highlightthickness=1, relief=tk.RAISED)
    style.configure('TNotebook.Tab', background=LIGHT_BG, foreground=LIGHT_FG, padding=[5, 2], borderwidth=1)
    style.map('TNotebook.Tab', background=[('selected', LIGHT_WIDGET_BG)], foreground=[('selected', LIGHT_FG)]) # White selected tab

    style.configure('Treeview', background=LIGHT_WIDGET_BG, foreground=LIGHT_FG, fieldbackground=LIGHT_WIDGET_BG, rowheight=25)
    style.map('Treeview', background=[('selected', LIGHT_SELECT_BG)], foreground=[('selected', LIGHT_SELECT_FG)])
    style.configure('Treeview.Heading', background=LIGHT_BG, foreground=LIGHT_FG, relief='raised', borderwidth=1)
    style.map('Treeview.Heading', background=[('active', LIGHT_BUTTON_ACTIVE_BG)])

    style.configure('Vertical.TScrollbar', background=LIGHT_BG, troughcolor=LIGHT_SCROLL_TROUGH, bordercolor=LIGHT_BG, arrowcolor=LIGHT_FG)
    style.map('Vertical.TScrollbar', background=[('active', LIGHT_BUTTON_ACTIVE_BG)])
    style.configure('Horizontal.TScrollbar', background=LIGHT_BG, troughcolor=LIGHT_SCROLL_TROUGH, bordercolor=LIGHT_BG, arrowcolor=LIGHT_FG)
    style.map('Horizontal.TScrollbar', background=[('active', LIGHT_BUTTON_ACTIVE_BG)])

    style.configure('TSpinbox', fieldbackground=LIGHT_WIDGET_BG, background=LIGHT_BUTTON_BG, foreground=LIGHT_FG, arrowcolor=LIGHT_FG, insertcolor=LIGHT_INSERT_BG, borderwidth=1, highlightthickness=1, bordercolor=LIGHT_OUTLINE, relief=tk.SUNKEN)
    style.map('TSpinbox', background=[('active', LIGHT_BUTTON_ACTIVE_BG)])

    style.configure('TLabelframe', background=LIGHT_BG, bordercolor=LIGHT_OUTLINE)
    style.configure('TLabelframe.Label', background=LIGHT_BG, foreground=LIGHT_FG)

    # Reset tk Widget Options
    root.option_add('*background', LIGHT_BG)
    root.option_add('*foreground', LIGHT_FG)
    root.option_add('*highlightBackground', LIGHT_BG)
    root.option_add('*highlightColor', LIGHT_FG) # Use foreground for highlight border
    root.option_add('*highlightThickness', 1)



# --- Tooltip Helper Class ---
class Tooltip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.id = None # Initialize id attribute
        self.x = self.y = 0 # Initialize coordinates
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave) # Hide tooltip on click

    def enter(self, event=None):
        # Store coordinates relative to the screen from the event
        self.x = event.x_root + 10
        self.y = event.y_root + 10
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule() # Cancel any pending schedules
        self.id = self.widget.after(500, self.showtip) # Schedule showtip after 500ms

    def unschedule(self):
        id = getattr(self, 'id', None)
        if id:
            self.widget.after_cancel(id)
            self.id = None

    def showtip(self):
        """Display the tooltip window."""
        if self.tooltip_window: # Avoid creating multiple tooltips
            return
        # Creates a toplevel window
        self.tooltip_window = tk.Toplevel(self.widget)
        # Removes the window decorations (title bar, borders)
        self.tooltip_window.wm_overrideredirect(True)
        # Position the tooltip window using the stored screen coordinates
        self.tooltip_window.wm_geometry(f"+{self.x}+{self.y}")
        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                       background=DARK_WIDGET_BG, foreground=DARK_FG, relief='solid', borderwidth=1,
                       font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        """Hide the tooltip window."""
        tw = self.tooltip_window
        self.tooltip_window = None # Reset the reference
        if tw:
            # Check if window exists before destroying
            try:
                if tw.winfo_exists():
                    tw.destroy()
            except tk.TclError: # Handle cases where the window might already be gone
                pass

# --- End Tooltip Helper Class ---


class OCIOGenGUI:
    def __init__(self, master):
        self.master = master
        master.title("OCIO Config Generator GUI")
        # Set a minimum size
        master.minsize(800, 650) # Increased size for Treeview

        # --- Tkinter Variable Setup ---
        self._setup_variables()

        # --- Load Initial Config ---
        try:
            # Load initial config state by creating an OCIOConfig instance without initial_data
            # This forces it to load from files/package data.
            initial_config_loader = OCIOConfig() # Loads defaults
            self.initial_settings = initial_config_loader.settings
            self.initial_roles = OrderedDict(initial_config_loader.roles)
            # Store colorspace objects created by the initial loader
            self.colorspace_objects = initial_config_loader.colorspaces[:]
            # We also need the raw colorspace definitions for the final generation step
            # Let's load them separately here as the loader doesn't expose the raw list directly.
            self.raw_colorspace_definitions = self._load_raw_colorspace_defs()
            if not self.raw_colorspace_definitions:
                 raise ValueError("Could not load raw colorspace definitions from colorspaces.yaml")

            # Note: _update_valid_cs_names and _update_filtered_lists will be called
            # *after* Tkinter vars are set in _populate_initial_values, using self.colorspace_objects
        except Exception as e:
            messagebox.showerror("Config Load Error", f"Failed to load initial configuration: {e}")
            master.quit()
            return

        # --- GUI Setup ---
        self.notebook = ttk.Notebook(master)
        # View Transform Treeview state
        self.treeview_edit_widget = None # To track the current editing widget
        self.treeview_edit_details = None # Store details of the widget being edited
        self.treeview_item_data = {} # Store extra data per item ID {item_id: {'type': 'LUT'/'Mutated', 'source_cs': '...', 'source_display': '...'}}
        self._drag_data = {"items": [], "start_y": 0} # Initialize drag data storage for LUT tree

        # Roles Treeview state
        self.roles_tree = None # Placeholder for the roles Treeview widget
        self.roles_tree_edit_widget = None
        self.roles_tree_edit_details = None
        # self.roles_tree_item_data = {} # Might not be needed if role name is key
        self._roles_drag_data = {"items": [], "start_y": 0} # Initialize drag data storage for roles tree

        # --- Tab 1: General Settings ---
        self.tab_general = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_general, text='General Settings')
        self._create_general_tab()

        # --- Tab 2: Colorspaces & Roles ---
        self.tab_cs_roles = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_cs_roles, text='Colorspaces & Roles')
        self._create_cs_roles_tab()

        # --- Tab 3: View Transforms ---
        self.tab_view_transforms = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.tab_view_transforms, text='View Transforms')
        self._create_view_transforms_tab()

        self.notebook.pack(expand=True, fill='both', padx=10, pady=5)

        # --- Bottom Frame ---
        self.bottom_frame = ttk.Frame(master)
        self.bottom_frame.pack(fill='x', padx=10, pady=(5, 10))
        self.bottom_frame.columnconfigure(1, weight=1) # Allow entry to expand

        # Output Directory Row
        ttk.Label(self.bottom_frame, text="Output Directory:").grid(row=0, column=0, sticky='w', pady=(0, 5))
        self.output_dir_entry = ttk.Entry(self.bottom_frame, textvariable=self.output_dir_var)
        self.output_dir_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=(0, 5))
        Tooltip(self.output_dir_entry, "The directory where the config folder will be created.")
        self.output_dir_browse_btn = ttk.Button(self.bottom_frame, text="Browse...", command=self._browse_output_path)
        self.output_dir_browse_btn.grid(row=0, column=2, sticky='w', padx=(0, 5), pady=(0, 5))
        Tooltip(self.output_dir_browse_btn, "Browse for the output directory.")
        # Add select all binding (Ctrl+A / Cmd+A)
        self.output_dir_entry.bind_class("TEntry", "<Control-a>", lambda event: event.widget.select_range(0, 'end'))
        self.output_dir_entry.bind_class("TEntry", "<Command-a>", lambda event: event.widget.select_range(0, 'end')) # macOS


        # Generate Button Row
        self.generate_button = ttk.Button(self.bottom_frame, text="Generate Config", command=self._generate_config)
        self.generate_button.grid(row=1, column=0, sticky='w', pady=(5, 0))
        Tooltip(self.generate_button, "Generate the OCIO config file based on the current settings and selections.")

        # Status Bar/Log Area (simplified for now)
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.bottom_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w')
        self.status_label.grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=(5, 0))
        self.status_var.set("Ready.")
        # Dark Mode Toggle
        self.dark_mode_checkbox = ttk.Checkbutton(self.bottom_frame, text="Dark Mode", variable=self.dark_mode_var, command=self._toggle_theme)
        self.dark_mode_checkbox.grid(row=1, column=3, sticky='e', padx=(10, 0), pady=(5, 0))
        Tooltip(self.dark_mode_checkbox, "Toggle between dark and light UI themes.")


        # --- Populate Initial Values & Set Callbacks ---
        self._populate_initial_values() # Sets vars, updates lists
        self._setup_callbacks()
        # Apply initial theme
        self._toggle_theme()

    def _load_raw_colorspace_defs(self):
        """Loads the raw list of dictionaries from colorspaces.yaml using importlib.resources."""
        try:
            # Access colorspaces.yaml relative to the 'ociogen.data' subpackage
            cs_path_ref = importlib.resources.files('ociogen.data').joinpath('colorspaces.yaml')
            with cs_path_ref.open('r', encoding='utf-8') as f:
                # Use standard SafeLoader here, as we don't need IncludeLoader's path logic
                # for this specific file (it's not the main config file)
                return yaml.safe_load(f)
        except FileNotFoundError:
            print("Error: colorspaces.yaml not found in package data.")
            return None
        except Exception as e:
            print(f"Error loading raw colorspace definitions from package data: {e}")
            return None

    def _setup_variables(self):
        """Initialize tkinter control variables."""
        # General Settings Tab
        self.config_name_var = tk.StringVar()
        self.config_description_text_widget = None # Placeholder for tk.Text widget

        self.ocio_version_var = tk.IntVar()
        self.use_shortnames_var = tk.BooleanVar()
        self.enable_descriptions_var = tk.BooleanVar()
        self.verbose_descriptions_var = tk.BooleanVar()
        self.enable_builtins_var = tk.BooleanVar()
        self.enable_encoding_var = tk.BooleanVar()
        self.enable_aliases_var = tk.BooleanVar()
        self.spi1d_precision_var = tk.IntVar()
        self.category_folder_vars = {
            'work': tk.StringVar(),
            'camera': tk.StringVar(),
            'display': tk.StringVar(),
            'image': tk.StringVar()
        }

        # Colorspaces & Roles Tab
        self.ref_cs_var = tk.StringVar()
        # Roles are now managed by the Treeview, self.role_vars is removed

        # View Transforms Tab
        self.lut_search_path_var = tk.StringVar()
        self.lut_pattern_var = tk.StringVar()

        self.output_dir_var = tk.StringVar()

        self.dark_mode_var = tk.BooleanVar(value=True) # Default to dark mode ON
        
    def _create_general_tab(self):
        """Create widgets for the General Settings tab."""
        frame = self.tab_general
        frame.columnconfigure(1, weight=1) # Allow entry fields to expand

        # Config Name
        ttk.Label(frame, text="Config Name:").grid(row=0, column=0, sticky='w', pady=2)
        self.config_name_entry = ttk.Entry(frame, textvariable=self.config_name_var)
        self.config_name_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        Tooltip(self.config_name_entry, "The OCIO config and LUTs will be placed in a folder with this name.")
        # Config Description
        ttk.Label(frame, text="Config Description:").grid(row=1, column=0, sticky='nw', pady=2) # Use 'nw' for top alignment
        desc_frame = ttk.Frame(frame) # Frame to hold text widget and scrollbar
        desc_frame.grid(row=1, column=1, sticky='nsew', padx=5, pady=2)
        desc_frame.rowconfigure(0, weight=1)
        desc_frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1) # Allow description row to expand vertically

        self.config_description_text_widget = tk.Text(desc_frame, height=4, wrap=tk.WORD, undo=True,
                                                    background=DARK_WIDGET_BG, foreground=DARK_FG,
                                                    insertbackground=DARK_INSERT_BG, # Cursor color
                                                    selectbackground=DARK_SELECT_BG,
                                                    selectforeground=DARK_SELECT_FG)
        self.config_description_text_widget.grid(row=0, column=0, sticky='nsew')
        Tooltip(self.config_description_text_widget, "A description for the generated OCIO configuration file (optional).")

        desc_scrollbar = ttk.Scrollbar(desc_frame, orient=tk.VERTICAL, command=self.config_description_text_widget.yview)
        desc_scrollbar.grid(row=0, column=1, sticky='ns')
        self.config_description_text_widget.config(yscrollcommand=desc_scrollbar.set)

        # Add standard text editing bindings
        self.config_description_text_widget.bind("<Control-a>", lambda e: self._select_all_text(e.widget))
        self.config_description_text_widget.bind("<Command-a>", lambda e: self._select_all_text(e.widget)) # macOS
        # Copy/Paste are usually handled by the system/Tkinter defaults



        # OCIO Version - ROW ADJUSTED
        ttk.Label(frame, text="OCIO Version:").grid(row=2, column=0, sticky='w', pady=2)
        version_frame = ttk.Frame(frame)
        version_frame.grid(row=2, column=1, sticky='w', padx=5, pady=2)
        self.ocio_v1_radio = ttk.Radiobutton(version_frame, text="1", variable=self.ocio_version_var, value=1)
        self.ocio_v1_radio.pack(side='left', padx=(0, 5))
        Tooltip(self.ocio_v1_radio, "Generate a config compatible with OCIO v1.0")
        self.ocio_v2_radio = ttk.Radiobutton(version_frame, text="2", variable=self.ocio_version_var, value=2)
        self.ocio_v2_radio.pack(side='left')
        Tooltip(self.ocio_v2_radio, "Generate a config compatible with OCIO v2.0 (enables more features)")

        # Checkboxes - ROW ADJUSTED
        self.use_shortnames_cb = ttk.Checkbutton(frame, text="Use Shortnames", variable=self.use_shortnames_var)
        self.use_shortnames_cb.grid(row=3, column=0, columnspan=2, sticky='w', pady=2)
        Tooltip(self.use_shortnames_cb, "Use a shorter name without spaces for the colorspace (defined as 'shortname' in each colorspace in colorspaces.yaml")

        self.enable_desc_cb = ttk.Checkbutton(frame, text="Enable Descriptions", variable=self.enable_descriptions_var)
        self.enable_desc_cb.grid(row=4, column=0, columnspan=2, sticky='w', pady=2)
        Tooltip(self.enable_desc_cb, "Include the 'description' entry for each colorspace in the generated config file.")

        self.verbose_desc_cb = ttk.Checkbutton(frame, text="Verbose Descriptions", variable=self.verbose_descriptions_var)
        self.verbose_desc_cb.grid(row=5, column=0, columnspan=2, sticky='w', padx=(20, 0), pady=2) # Indent
        Tooltip(self.verbose_desc_cb, "Include more verbose descriptions (e.g., transform details, whitepapers) if 'Enable Descriptions' is checked.")

        self.enable_builtins_cb = ttk.Checkbutton(frame, text="Enable Built-in Transforms (OCIOv2)", variable=self.enable_builtins_var)
        self.enable_builtins_cb.grid(row=6, column=0, columnspan=2, sticky='w', pady=2)
        Tooltip(self.enable_builtins_cb, "The generated OCIO config will use formula based transforms like LogCameraTransform. WARNING: these transforms are about 26x less precise than a low resolution spi1d LUT.")

        self.enable_encoding_cb = ttk.Checkbutton(frame, text="Enable Colorspace Encoding (OCIOv2)", variable=self.enable_encoding_var)
        self.enable_encoding_cb.grid(row=7, column=0, columnspan=2, sticky='w', pady=2)
        Tooltip(self.enable_encoding_cb, "Include the 'encoding' attribute for colorspaces (e.g., 'scene-linear', 'log', 'display-linear').")

        self.enable_aliases_cb = ttk.Checkbutton(frame, text="Enable Colorspace Aliases (OCIOv2)", variable=self.enable_aliases_var)
        self.enable_aliases_cb.grid(row=8, column=0, columnspan=2, sticky='w', pady=2)
        Tooltip(self.enable_aliases_cb, "Include the 'aliases' attribute for colorspaces.")

        # LUT Precision - ROW ADJUSTED
        ttk.Label(frame, text="SPI1D LUT Precision (2^n):").grid(row=9, column=0, sticky='w', pady=2)
        # Using Spinbox for constrained integer input
        self.spi1d_spinbox = ttk.Spinbox(frame, from_=8, to=16, textvariable=self.spi1d_precision_var, width=5)
        self.spi1d_spinbox.grid(row=9, column=1, sticky='w', padx=5, pady=2)
        Tooltip(self.spi1d_spinbox, "The precision (table size = 2^n) for generated 1D LUTs (.spi1d). Higher values mean more precision but larger files.")

        # Category Folder Names - ROW ADJUSTED
        cat_frame = ttk.LabelFrame(frame, text="Category Folder Names", padding="5")
        cat_frame.grid(row=10, column=0, columnspan=2, sticky='ew', pady=(10, 2))
        Tooltip(cat_frame, "Define the folder names used when organizing colorspaces by category in applications like Nuke.")
        cat_frame.columnconfigure(1, weight=1)

        row_idx = 0
        for key, var in self.category_folder_vars.items():
            ttk.Label(cat_frame, text=f"{key.capitalize()}:").grid(row=row_idx, column=0, sticky='w', pady=1)
            entry = ttk.Entry(cat_frame, textvariable=var)
            entry.grid(row=row_idx, column=1, sticky='ew', padx=5, pady=1)
            Tooltip(entry, f"Folder name for the '{key}' category.")
            row_idx += 1

    def _create_cs_roles_tab(self):
        """Create widgets for the Colorspaces & Roles tab."""
        frame = self.tab_cs_roles
        frame.columnconfigure(0, weight=1) # Left column (listbox)
        frame.columnconfigure(1, weight=1) # Right column (roles)
        frame.rowconfigure(1, weight=1)    # Allow listbox/roles frame to expand vertically

        # --- Left Column: Reference and Active Colorspaces ---
        left_frame = ttk.Frame(frame)
        left_frame.grid(row=0, column=0, rowspan=2, sticky='nsew', padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(3, weight=1) # Allow listbox frame to expand

        # Reference Colorspace
        ttk.Label(left_frame, text="Reference Colorspace (Scene-Linear):").grid(row=0, column=0, sticky='w', pady=(0, 2))
        self.ref_cs_combo = ttk.Combobox(left_frame, textvariable=self.ref_cs_var, state='readonly', width=40)
        self.ref_cs_combo.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        Tooltip(self.ref_cs_combo, "Select the primary scene-linear colorspace to be used as the reference for transforms.")

        # Active Colorspaces Listbox
        ttk.Label(left_frame, text="Active Colorspaces (Ctrl+A Toggles All):").grid(row=2, column=0, sticky='nw', pady=(0, 2)) # Updated label
        listbox_frame = ttk.Frame(left_frame)
        listbox_frame.grid(row=3, column=0, sticky='nsew')
        listbox_frame.rowconfigure(0, weight=1)
        listbox_frame.columnconfigure(0, weight=1)

        self.active_cs_listbox = tk.Listbox(listbox_frame, selectmode=tk.EXTENDED, exportselection=False, width=40, height=15,
                                           background=DARK_WIDGET_BG, foreground=DARK_FG,
                                           selectbackground=DARK_SELECT_BG,
                                           selectforeground=DARK_SELECT_FG) # Set initial height
        self.active_cs_listbox.grid(row=0, column=0, sticky='nsew')
        Tooltip(self.active_cs_listbox, "Select the colorspaces to include in the generated config.\n(Use Ctrl+Click or Shift+Click for multiple selection. Ctrl+A toggles all.)")
        # Bind Ctrl+A
        self.active_cs_listbox.bind("<Control-a>", self._toggle_select_all_cs)
        self.active_cs_listbox.bind("<Command-a>", self._toggle_select_all_cs) # For macOS


        # Scrollbars for Listbox
        ysb = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.active_cs_listbox.yview)
        ysb.grid(row=0, column=1, sticky='ns')
        xsb = ttk.Scrollbar(listbox_frame, orient=tk.HORIZONTAL, command=self.active_cs_listbox.xview)
        xsb.grid(row=1, column=0, sticky='ew')
        self.active_cs_listbox.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)

        # Select/Deselect Buttons
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=4, column=0, sticky='ew', pady=(5, 0))
        select_all_btn = ttk.Button(button_frame, text="Select All", command=self._select_all_cs)
        select_all_btn.pack(side='left', padx=(0, 5))
        Tooltip(select_all_btn, "Select all colorspaces in the list above.")
        deselect_all_btn = ttk.Button(button_frame, text="Deselect All", command=self._deselect_all_cs)
        deselect_all_btn.pack(side='left')
        Tooltip(deselect_all_btn, "Deselect all colorspaces in the list above.")

        # --- Right Column: Roles Treeview ---
        roles_frame = ttk.Frame(frame)
        roles_frame.grid(row=0, column=1, rowspan=2, sticky='nsew', padx=(5, 0))
        roles_frame.columnconfigure(0, weight=1)
        roles_frame.rowconfigure(1, weight=1) # Allow treeview to expand

        ttk.Label(roles_frame, text="Roles Configuration:").grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 2))

        roles_tree_frame = ttk.Frame(roles_frame)
        roles_tree_frame.grid(row=1, column=0, columnspan=2, sticky='nsew')
        roles_tree_frame.columnconfigure(0, weight=1)
        roles_tree_frame.rowconfigure(0, weight=1)

        # Define columns for the Roles Treeview
        roles_columns = ('role_name', 'assigned_cs')
        self.roles_tree = ttk.Treeview(roles_tree_frame, columns=roles_columns, show='headings', height=10)
        Tooltip(self.roles_tree, "Manage OCIO roles.\nDouble-click to edit Name or Assigned Colorspace.\nDrag to reorder. Right-click for options.")

        # Define headings
        self.roles_tree.heading('role_name', text='Role Name', anchor='w')
        self.roles_tree.heading('assigned_cs', text='Assigned Colorspace', anchor='w')

        # Define column widths (adjust as needed)
        self.roles_tree.column('role_name', width=150, anchor='w')
        self.roles_tree.column('assigned_cs', width=250, anchor='w')

        self.roles_tree.grid(row=0, column=0, sticky='nsew')

        # Scrollbars for Roles Treeview
        roles_ysb = ttk.Scrollbar(roles_tree_frame, orient=tk.VERTICAL, command=self.roles_tree.yview)
        roles_ysb.grid(row=0, column=1, sticky='ns')
        roles_xsb = ttk.Scrollbar(roles_tree_frame, orient=tk.HORIZONTAL, command=self.roles_tree.xview)
        roles_xsb.grid(row=1, column=0, sticky='ew')
        self.roles_tree.configure(yscrollcommand=roles_ysb.set, xscrollcommand=roles_xsb.set)

        # Buttons for Add/Delete Role
        roles_button_frame = ttk.Frame(roles_frame)
        roles_button_frame.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(5, 0))
        add_role_btn = ttk.Button(roles_button_frame, text="Add Role", command=self._add_role)
        add_role_btn.pack(side='left', padx=(0, 5))
        Tooltip(add_role_btn, "Add a new role to the list.")
        delete_role_btn = ttk.Button(roles_button_frame, text="Delete Selected Role(s)", command=self._delete_selected_roles)
        delete_role_btn.pack(side='left')
        Tooltip(delete_role_btn, "Delete the selected role(s) from the list.")

        # --- Bind Events for Roles Treeview ---
        self.roles_tree.bind("<Double-1>", self._on_roles_tree_double_click)
        self.roles_tree.bind("<Button-1>", self._handle_roles_tree_click) # Handles click outside edit widget
        self.roles_tree.bind("<ButtonPress-1>", self._on_roles_tree_drag_start, add='+')
        self.roles_tree.bind("<B1-Motion>", self._on_roles_tree_drag_motion)
        self.roles_tree.bind("<ButtonRelease-1>", self._on_roles_tree_drag_drop)
        # self.roles_tree.bind("<Button-3>", self._show_roles_tree_context_menu) # Optional: Add context menu later if needed
        self.roles_tree.bind("<Delete>", self._delete_selected_roles) # Bind Delete key


    def _create_view_transforms_tab(self):
        """Create widgets for the View Transforms tab."""
        frame = self.tab_view_transforms
        frame.columnconfigure(0, weight=1) # Allow treeview frame to expand
        frame.rowconfigure(2, weight=1)    # Allow treeview frame to expand vertically

        # --- Top Settings ---
        settings_frame = ttk.Frame(frame)
        settings_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)

        # LUT Search Path
        ttk.Label(settings_frame, text="LUT Search Path:").grid(row=0, column=0, sticky='w', pady=2)
        # Store the entry widget for potential binding later if needed
        self.lut_path_entry = ttk.Entry(settings_frame, textvariable=self.lut_search_path_var)
        self.lut_path_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        Tooltip(self.lut_path_entry, "Directory to search for View Transform LUTs.\nRelative paths are resolved from the Current Working Directory.\nAbsolute paths are used as-is.")
        # Add select all binding (Ctrl+A / Cmd+A)
        self.lut_path_entry.bind_class("TEntry", "<Control-a>", lambda event: event.widget.select_range(0, 'end'))
        self.lut_path_entry.bind_class("TEntry", "<Command-a>", lambda event: event.widget.select_range(0, 'end')) # macOS

        browse_button = ttk.Button(settings_frame, text="Browse...", command=self._browse_lut_path)
        browse_button.grid(row=0, column=2, sticky='w', padx=(0, 5), pady=2)
        Tooltip(browse_button, "Browse for the LUT search directory.")

        # LUT Filename Pattern
        ttk.Label(settings_frame, text="LUT Filename Pattern:").grid(row=1, column=0, sticky='w', pady=2)
        pattern_entry = ttk.Entry(settings_frame, textvariable=self.lut_pattern_var)
        pattern_entry.grid(row=1, column=1, columnspan=2, sticky='ew', padx=5, pady=2)
        Tooltip(pattern_entry, "Filename pattern to automatically parse View, Display, and Shaper spaces from LUT filenames.\nUse placeholders: {viewName}, {displaySpace}, {shaperSpace}.\nExample: {viewName}__{shaperSpace}__to__{displaySpace}")

        # Refresh Button
        refresh_button = ttk.Button(frame, text="Refresh Discovered LUTs", command=self._discover_luts_for_gui)
        refresh_button.grid(row=1, column=0, sticky='w', pady=(0, 5))
        Tooltip(refresh_button, "Scan the LUT Search Path using the Filename Pattern to find and parse LUTs.")

        # --- Treeview for Discovered LUTs ---
        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=2, column=0, sticky='nsew')
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Add 'type' and 'source' columns
        columns = ('type', 'source', 'view', 'shaper', 'display_space', 'status')
        self.lut_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
        Tooltip(self.lut_tree, "List of discovered LUTs based on the path and pattern.\nDouble-click View, Shaper, or Display cells to edit.\nRed entries indicate errors or missing information.")

        # Define headings
        self.lut_tree.heading('type', text='Type', anchor='w')
        self.lut_tree.heading('source', text='Source', anchor='w') # Was 'filename'
        self.lut_tree.heading('view', text='View Name', anchor='w')
        self.lut_tree.heading('shaper', text='Shaper Space', anchor='w')
        self.lut_tree.heading('display_space', text='Display Space', anchor='w')
        self.lut_tree.heading('status', text='Status', anchor='w')

        # Define column widths (adjust as needed)
        self.lut_tree.column('type', width=80, anchor='w', stretch=tk.NO)
        self.lut_tree.column('source', width=250, anchor='w') # Combined filename/source view
        self.lut_tree.column('view', width=150, anchor='w')
        self.lut_tree.column('shaper', width=150, anchor='w')
        self.lut_tree.column('display_space', width=150, anchor='w')
        self.lut_tree.column('status', width=150, anchor='w')

        self.lut_tree.grid(row=0, column=0, sticky='nsew')

        # Scrollbars for Treeview
        tree_ysb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.lut_tree.yview)
        tree_ysb.grid(row=0, column=1, sticky='ns')
        tree_xsb = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.lut_tree.xview)
        tree_xsb.grid(row=1, column=0, sticky='ew')
        self.lut_tree.configure(yscrollcommand=tree_ysb.set, xscrollcommand=tree_xsb.set)


        # Bind double-click for editing
        self.lut_tree.bind("<Double-1>", self._on_treeview_double_click)
        # Bind single click on tree to potentially cancel edit
        self.lut_tree.bind("<Button-1>", self._handle_tree_click) # Existing click handler
        # Add bindings for drag-and-drop
        self.lut_tree.bind("<ButtonPress-1>", self._on_treeview_drag_start, add='+') # Use add='+' to not override existing bind
        self.lut_tree.bind("<B1-Motion>", self._on_treeview_drag_motion)
        self.lut_tree.bind("<ButtonRelease-1>", self._on_treeview_drag_drop)
        self._drag_data = {"items": [], "start_y": 0} # Initialize drag data storage
        # Bind right-click for context menu
        self.lut_tree.bind("<Button-3>", self._show_treeview_context_menu) # Button-3 is typically right-click
        # Bind Delete key
        self.lut_tree.bind("<Delete>", self._delete_selected_view)
        # Add tag for user-added mutations
        self.lut_tree.tag_configure('mutated_user', foreground='cyan') # Example style


    def _populate_initial_values(self):
        """Populate GUI widgets with values from loaded OCIOConfig."""
        # Use the initial settings loaded during GUI initialization
        settings = self.initial_settings
        if not settings:
            self.status_var.set("Error: No initial settings loaded.")
            return

        # --- General Settings ---
        # Validate and set Tkinter variables
        self.config_name_var.set(self._validate_setting(settings, "config_name", str, "generated_config"))
        self.ocio_version_var.set(self._validate_setting(settings, "ocio_version_major", int, 1))
        self.use_shortnames_var.set(self._validate_setting(settings, "use_shortnames", bool, True))
        self.enable_descriptions_var.set(self._validate_setting(settings, "enable_descriptions", bool, False))
        self.verbose_descriptions_var.set(self._validate_setting(settings, "verbose_descriptions", bool, False))
        self.enable_builtins_var.set(self._validate_setting(settings, "enable_builtins", bool, False))
        self.enable_encoding_var.set(self._validate_setting(settings, "enable_colorspace_encoding", bool, False))
        self.enable_aliases_var.set(self._validate_setting(settings, "enable_colorspace_aliases", bool, False))
        self.spi1d_precision_var.set(self._validate_setting(settings, "spi1d_lut_precision", int, 13))

        # Config Description (populate Text widget)
        config_desc = self._validate_setting(settings, "config_description", str, "")
        if self.config_description_text_widget: # Check if widget exists
            self.config_description_text_widget.delete("1.0", tk.END) # Clear existing content
            self.config_description_text_widget.insert("1.0", config_desc) # Insert new content

        # Category Folders - Validate structure
        category_folder_names_raw = settings.get('category_folder_names', [])
        loaded_cats = {}
        default_cats = {k: k.capitalize() + " Spaces" for k in self.category_folder_vars.keys()}
        if isinstance(category_folder_names_raw, list):
            for item in category_folder_names_raw:
                if isinstance(item, dict) and len(item) == 1:
                    key, value = next(iter(item.items()))
                    if isinstance(key, str) and isinstance(value, str) and key in self.category_folder_vars:
                        loaded_cats[key] = value
                    else:
                        print(f"Warning: Invalid item format or key/value type in 'category_folder_names': {item}. Skipping.")
                else:
                    print(f"Warning: Invalid item format in 'category_folder_names': {item}. Expected single key-value dict. Skipping.")
        else:
            print(f"Warning: Invalid type for 'category_folder_names'. Expected list, got {type(category_folder_names_raw).__name__}. Using defaults.")
            loaded_cats = default_cats # Use defaults if structure is wrong

        for key, var in self.category_folder_vars.items():
            var.set(loaded_cats.get(key, default_cats[key])) # Use loaded value or default

        # --- Update derived lists AFTER setting Tkinter vars ---
        # Need to call this *before* setting reference CS etc.
        self._update_valid_cs_names(self.colorspace_objects)
        self._update_filtered_lists()

        # --- Colorspaces & Roles ---
        # Populate dropdowns/lists BEFORE setting initial values
        self._update_ref_cs_dropdown()
        self._update_active_cs_listbox() # Populate active listbox

        # --- Populate Roles Treeview ---
        self._populate_roles_treeview() # New method call

        # Set initial reference selection (robustly)
        initial_ref_name = settings.get('reference_colorspace')
        if initial_ref_name:
            # Find the display name corresponding to the initial underlying name
            # Use self.colorspace_objects which were populated from the initial load
            initial_ref_obj = self._find_cs_by_name_or_shortname(initial_ref_name)
            if initial_ref_obj:
                 initial_display_name = self._get_display_name(initial_ref_obj)
                 # Check if the calculated display name exists in the *current* dropdown values
                 if initial_display_name in self.ref_cs_combo['values']:
                     self.ref_cs_var.set(initial_display_name)
                 else:
                     # This might happen if the initial ref space isn't scene-linear
                     print(f"Warning: Initial reference colorspace '{initial_ref_name}' (display: '{initial_display_name}') not found in filtered dropdown values.")
                     # Attempt to set based on underlying name if that exists in list (unlikely if filtered)
                     if initial_ref_name in self.ref_cs_combo['values']:
                          self.ref_cs_var.set(initial_ref_name)
                     elif self.ref_cs_combo['values']:
                          self.ref_cs_var.set(self.ref_cs_combo['values'][0]) # Fallback
            else:
                 print(f"Warning: Initial reference colorspace '{initial_ref_name}' not found in loaded colorspaces.")
                 if self.ref_cs_combo['values']:
                      self.ref_cs_var.set(self.ref_cs_combo['values'][0]) # Fallback


        # Role selection is now handled by the treeview population


        # --- Output Directory ---
        output_location = self._validate_setting(settings, "config_location", str, "~/Desktop")
        self.output_dir_var.set(os.path.expanduser(output_location)) # Expand ~

        # --- View Transforms ---
        vt_settings_raw = settings.get('view_transform_settings', {})
        vt_settings = {}
        if isinstance(vt_settings_raw, dict):
             vt_settings = vt_settings_raw # Use if it's a dict
        else:
             print(f"Warning: Invalid type for 'view_transform_settings'. Expected dict, got {type(vt_settings_raw).__name__}. Using defaults.")
             # Defaults will be handled by the _validate_setting calls below

        self.lut_search_path_var.set(self._validate_setting(vt_settings, 'lut_search_path', str, 'luts/'))
        self.lut_pattern_var.set(self._validate_setting(vt_settings, 'lut_filename_pattern', str, '{viewName}__{shaperSpace}__to__{displaySpace}'))
        self._discover_luts_for_gui() # Perform initial discovery

        # --- Update Widget States ---
        self._update_widget_states() # Call AFTER vars are set

        self.status_var.set("Initial values populated.")


    def _validate_setting(self, settings, key, expected_type, default_value):
        """Helper to validate setting type and return value or default."""
        value = settings.get(key, default_value)
        if not isinstance(value, expected_type):
            # Special case for bool: allow 0/1 as int
            if expected_type is bool and isinstance(value, int) and value in (0, 1):
                print(f"Warning: Setting '{key}' is an integer ({value}), converting to boolean.")
                value = bool(value)
            # Special case for int: allow float that is integer-like
            elif expected_type is int and isinstance(value, float) and value.is_integer():
                 print(f"Warning: Setting '{key}' is a float ({value}), converting to integer.")
                 value = int(value)
            else:
                print(f"Warning: Invalid type for setting '{key}'. Expected {expected_type.__name__}, got {type(value).__name__} ('{value}'). Using default '{default_value}'.")
                value = default_value
        # Additional check for OCIO version range
        if key == "ocio_version_major" and value not in (1, 2):
             print(f"Warning: Invalid value for setting '{key}'. Expected 1 or 2, got '{value}'. Using default '{default_value}'.")
             value = default_value
        return value

    def _get_display_name(self, cs_obj):
        """Gets the display name for a colorspace object based on use_shortnames."""
        if not cs_obj: return ""
        use_short = self.use_shortnames_var.get()
        if use_short and cs_obj.shortname:
            return cs_obj.shortname
        return cs_obj.name

    def _find_cs_by_name_or_shortname(self, name_or_shortname):
        """Finds a colorspace object by its name or shortname from the default handler."""
        if not name_or_shortname: return None
        # Use the initially loaded handler's method for consistency
        # Need to iterate through the stored objects
        for cs_obj in self.colorspace_objects:
             if cs_obj.name == name_or_shortname or cs_obj.shortname == name_or_shortname:
                 return cs_obj
        # Fallback check using the handler's method (might be slightly different if active list changes)
        # return initial_config_loader._get_colorspace_from_name(name_or_shortname) # Don't use temporary loader here
        return None


    def _update_valid_cs_names(self, colorspace_objects):
        """Update the list of valid colorspace names (short or long) from Colorspace objects."""
        self.valid_cs_names = set()
        for cs in colorspace_objects:
            self.valid_cs_names.add(cs.name)
            if cs.shortname:
                self.valid_cs_names.add(cs.shortname)
        # Also add *current* valid role names from the treeview
        current_role_names = self._get_current_role_names()
        self.valid_cs_names.update(current_role_names)
        # Add the underlying reference colorspace names from *current* roles
        if self.roles_tree:
            for role_name in current_role_names:
                 try:
                     values = self.roles_tree.item(role_name, 'values')
                     if len(values) > 1:
                         assigned_cs_display = values[1]
                         role_cs_name = self._get_underlying_cs_name(assigned_cs_display, resolve_role=False)
                         if role_cs_name:
                              self.valid_cs_names.add(role_cs_name)
                 except tk.TclError:
                     print(f"Warning: Could not get values for role '{role_name}' while updating valid names.")

    def _update_filtered_lists(self):
        """Pre-calculates filtered lists of colorspace names for performance."""
        self.all_cs_names = self._get_filtered_cs_names()
        self.scene_linear_cs_names = self._get_filtered_cs_names(encoding_filter='scene-linear')
        self.log_cs_names = self._get_filtered_cs_names(encoding_filter='log')
        self.display_cs_names = self._get_filtered_cs_names(category_filter='display')
        # Add *current* roles from treeview to log list for shaper space
        current_role_names = self._get_current_role_names()
        self.log_and_role_names = sorted(list(set(self.log_cs_names + list(current_role_names)))) # Convert tuple to list
        # Update list of all valid names (including current roles) for validation
        self._update_valid_cs_names(self.colorspace_objects) # Call this again to include current roles


    def _get_filtered_cs_names(self, encoding_filter=None, category_filter=None):
        """Gets a sorted list of colorspace display names, optionally filtered by encoding or category."""
        filtered_list = []
        for cs in self.colorspace_objects:
            include = True
            if encoding_filter and cs.encoding != encoding_filter:
                include = False
            if category_filter and cs.category != category_filter:
                 include = False
            if include:
                filtered_list.append(self._get_display_name(cs))
        return sorted(filtered_list)


    def _update_ref_cs_dropdown(self):
        """Updates the reference colorspace dropdown contents and selection."""
        display_names = self.scene_linear_cs_names # Use pre-filtered list
        current_selection = self.ref_cs_var.get()
        current_underlying = self._get_underlying_cs_name(current_selection, resolve_role=False) if current_selection else None

        self.ref_cs_combo['values'] = display_names

        # Try to preserve selection based on underlying name
        new_selection = ""
        if current_underlying:
            # Find the new display name for the same underlying colorspace
            cs_obj = self._find_cs_by_name_or_shortname(current_underlying)
            if cs_obj and cs_obj.encoding == 'scene-linear': # Ensure it's still in the list
                new_selection = self._get_display_name(cs_obj)

        # Set selection if found and valid, otherwise fallback
        if new_selection and new_selection in display_names:
             self.ref_cs_var.set(new_selection)
        elif display_names:
             # If previous selection is lost, try setting based on initial config value
             initial_ref_name = self.initial_settings.get('reference_colorspace') # Use stored initial settings
             initial_ref_obj = self._find_cs_by_name_or_shortname(initial_ref_name)
             if initial_ref_obj and initial_ref_obj.encoding == 'scene-linear':
                 initial_display_name = self._get_display_name(initial_ref_obj)
                 if initial_display_name in display_names:
                     self.ref_cs_var.set(initial_display_name)
                 else:
                     self.ref_cs_var.set(display_names[0]) # Fallback to first
             else:
                 self.ref_cs_var.set(display_names[0]) # Fallback to first
        else:
            self.ref_cs_var.set("") # Clear if no options


    def _update_active_cs_listbox(self):
        """Updates the active colorspace listbox contents and selection."""
        # Get current selections (by index)
        selected_indices = self.active_cs_listbox.curselection()
        # Store underlying names of selected items to preserve selection across name changes
        selected_underlying_names = set()
        for i in selected_indices:
             try: # Add try-except in case listbox is modified during iteration
                 display_name = self.active_cs_listbox.get(i)
                 underlying = self._get_underlying_cs_name(display_name, resolve_role=False)
                 if underlying: selected_underlying_names.add(underlying)
             except tk.TclError:
                 print(f"Warning: Could not get listbox item at index {i} during update.")


        # Clear the listbox
        self.active_cs_listbox.delete(0, tk.END)

        # Repopulate with potentially new display names using default handler's colorspaces
        display_name_map = {} # Map display name back to original object name/shortname
        new_selection_indices = []
        # Sort based on the current display name for consistent list order
        sorted_cs_objects = sorted(self.colorspace_objects, key=lambda cs: self._get_display_name(cs))

        for idx, cs_obj in enumerate(sorted_cs_objects):
            display_name = self._get_display_name(cs_obj)
            self.active_cs_listbox.insert(tk.END, display_name)
            # Store mapping (use shortname if available and unique, else name)
            key = cs_obj.shortname if cs_obj.shortname else cs_obj.name
            display_name_map[display_name] = key
            underlying_name = self._get_underlying_cs_name(display_name, resolve_role=False)

            # Check if this item's underlying name was previously selected
            if underlying_name in selected_underlying_names:
                 new_selection_indices.append(idx)

        # Reapply selection
        for idx in new_selection_indices:
            self.active_cs_listbox.selection_set(idx)

        # Select initial active colorspaces if listbox was just populated and nothing was selected before
        # Use the active_colorspaces loaded during GUI initialization
        initial_active_list = self.initial_settings.get('active_colorspaces') # Get from stored initial settings
        if not selected_indices and not new_selection_indices and initial_active_list is not None:
            initial_active_set = set(initial_active_list)
            for i in range(self.active_cs_listbox.size()):
                display_name = self.active_cs_listbox.get(i)
                # Check if the current display name OR the underlying shortname/name is in the initial set
                underlying_key = display_name_map.get(display_name)
                if display_name in initial_active_set or underlying_key in initial_active_set:
                    self.active_cs_listbox.selection_set(i)


    # _update_role_dropdowns removed as roles are now in Treeview


    def _select_all_cs(self):
        """Select all items in the active colorspace listbox."""
        self.active_cs_listbox.selection_set(0, tk.END)

    def _deselect_all_cs(self):
        """Deselect all items in the active colorspace listbox."""
        self.active_cs_listbox.selection_clear(0, tk.END)

    def _toggle_select_all_cs(self, event=None):
        """Toggles selection of all items in the active colorspace listbox."""
        num_items = self.active_cs_listbox.size()
        num_selected = len(self.active_cs_listbox.curselection())

        if num_selected == num_items:
            self._deselect_all_cs()
        else:
            self._select_all_cs()
        return "break" # Prevents default Ctrl+A behavior (e.g., selecting text in entry)


    def _update_widget_states(self):
        """Enable/disable widgets based on the state of others."""
        # Verbose Descriptions state depends on Enable Descriptions
        verbose_state = tk.NORMAL if self.enable_descriptions_var.get() else tk.DISABLED
        if hasattr(self, 'verbose_desc_cb'): # Check if widget exists yet
             self.verbose_desc_cb.config(state=verbose_state)
             if not self.enable_descriptions_var.get():
                 self.verbose_descriptions_var.set(False) # Uncheck if disabled

        # OCIOv2 options state depends on OCIO Version
        ocio_v2_state = tk.NORMAL if self.ocio_version_var.get() == 2 else tk.DISABLED
        if hasattr(self, 'enable_builtins_cb'): # Check if widgets exist yet
            self.enable_builtins_cb.config(state=ocio_v2_state)
            self.enable_encoding_cb.config(state=ocio_v2_state)
            self.enable_aliases_cb.config(state=ocio_v2_state)
            if self.ocio_version_var.get() != 2:
                self.enable_builtins_var.set(False)
                self.enable_encoding_var.set(False)
                self.enable_aliases_var.set(False)


    def _setup_callbacks(self):
        """Setup callbacks for widget interactions."""
        # Update widget states when dependencies change
        self.enable_descriptions_var.trace_add("write", lambda *args: self._update_widget_states())
        self.ocio_version_var.trace_add("write", lambda *args: self._update_widget_states())
        # Update colorspace display names when use_shortnames changes
        self.use_shortnames_var.trace_add("write", lambda *args: self._update_colorspace_displays())
        # Update valid names when use_shortnames changes (for validation later)
        self.use_shortnames_var.trace_add("write", lambda *args: self._update_valid_cs_names(self.colorspace_objects))


    def _update_colorspace_displays(self):
        """Update display names in ref dropdown, active listbox, role dropdowns, and treeview."""
        # Update pre-filtered lists first
        self._update_filtered_lists()
        # Then update widgets
        self._update_ref_cs_dropdown()
        self._update_active_cs_listbox()
        # self._update_role_dropdowns() # Removed
        self._update_treeview_display_names()


    def _update_treeview_display_names(self):
        """Updates the display names in the Shaper and Display Space columns of the Treeview."""
        if not hasattr(self, 'lut_tree'): return # Treeview might not exist yet

        for item_id in self.lut_tree.get_children():
            values = list(self.lut_tree.item(item_id, 'values')) # Get current values as list
            # Indices: 0:filename, 1:view, 2:shaper, 3:display_space, 4:status
            shaper_current_display = values[2]
            display_current_display = values[3]

            # Update Shaper Space display name
            # Only update if not showing an INVALID/MISSING status message
            if not shaper_current_display.startswith(("INVALID:", "INVALID_ROLE:")) and not shaper_current_display == "MISSING":
                shaper_underlying = self._get_underlying_cs_name(shaper_current_display, resolve_role=True)
                if shaper_underlying: # Could be role or cs name/shortname
                    shaper_obj = self._find_cs_by_name_or_shortname(shaper_underlying)
                    if shaper_obj:
                        values[2] = self._get_display_name(shaper_obj)
                    # else: it's a role, keep current display name (which is the role name)

            # Update Display Space display name
            if not display_current_display.startswith("INVALID:"):
                display_underlying = self._get_underlying_cs_name(display_current_display, resolve_role=False)
                if display_underlying:
                    display_obj = self._find_cs_by_name_or_shortname(display_underlying)
                    if display_obj:
                        values[3] = self._get_display_name(display_obj)

            # Update the item in the treeview
            self.lut_tree.item(item_id, values=tuple(values))


    def _browse_lut_path(self):
        """Open directory browser for LUT search path."""
        # Use current value in the entry field as initial directory suggestion.
        # Default to current working directory if entry is empty or invalid.
        current_path_setting = self.lut_search_path_var.get()
        initial_dir = os.getcwd() # Default to CWD

        # Try to resolve the current path setting (relative to CWD or absolute)
        potential_path = current_path_setting
        if not os.path.isabs(potential_path):
             potential_path = os.path.abspath(os.path.join(os.getcwd(), potential_path))

        if os.path.isdir(potential_path):
            initial_dir = potential_path
        # If the path doesn't exist, check if its parent exists
        elif os.path.isdir(os.path.dirname(potential_path)):
             initial_dir = os.path.dirname(potential_path)
             
        directory = filedialog.askdirectory(initialdir=initial_dir, title="Select LUT Search Directory")
        if directory:
            # Always use the absolute path
            abs_path = os.path.abspath(directory)
            # Add trailing slash if not present (optional, but can be consistent)
            # if not abs_path.endswith(os.path.sep):
            #     abs_path += os.path.sep
            self.lut_search_path_var.set(abs_path)
            # Automatically refresh after browsing
            self._discover_luts_for_gui()


    def _discover_luts_for_gui(self):
        """Discover LUTs based on GUI path/pattern and populate Treeview."""
        self.status_var.set("Discovering LUTs...")
        # Clear existing items
        # Clear existing items and internal data store
        for item_id in self.lut_tree.get_children():
            self.lut_tree.delete(item_id)
        self.treeview_item_data.clear()

        search_path = self.lut_search_path_var.get()
        pattern = self.lut_pattern_var.get() # Pattern from GUI should NOT include extension
        # Resolve LUT search path: absolute or relative to CWD
        if os.path.isabs(search_path):
            full_search_dir = search_path
        else:
            # Interpret relative paths from the current working directory
            full_search_dir = os.path.abspath(os.path.join(os.getcwd(), search_path))

        if not os.path.isdir(full_search_dir):
            self.status_var.set(f"LUT directory not found: {full_search_dir}")
            return
        
        # --- Build Regex from Pattern (Using displaySpace) ---
        placeholders = {
            'viewName': r'(?P<viewName>.+)',
            'displaySpace': r'(?P<displaySpace>.+)', # Use displaySpace
            'shaperSpace': r'(?P<shaperSpace>.+?)' # Non-greedy
        }
        regex_pattern_str = re.escape(pattern) # Escape the literal parts of the pattern
        has_shaper_placeholder = False
        for key, regex_part in placeholders.items():
            placeholder_escaped = re.escape(f"{{{key}}}")
            if placeholder_escaped in regex_pattern_str:
                regex_pattern_str = regex_pattern_str.replace(placeholder_escaped, regex_part, 1)
                if key == 'shaperSpace': has_shaper_placeholder = True
        # Anchor the regex to match the whole name part (without extension)
        regex_pattern_str = f"^{regex_pattern_str}$"

        # --- Iterate and Parse ---
        lut_count = 0
        pattern_matched_count = 0
        lut_data_to_display = [] # List to hold data before inserting into treeview
        for filename in os.listdir(full_search_dir):
            filepath = os.path.join(full_search_dir, filename)
            if not os.path.isfile(filepath): continue

            name_part, ext = os.path.splitext(filename)
            if ext.lower() not in VALID_LUT_EXTENSIONS:
                continue # Skip files with invalid extensions

            lut_count += 1
            match = re.match(regex_pattern_str, name_part) # Match against name part only

            if match:
                # Pattern Matched - Parse and Validate
                pattern_matched_count += 1
                parsed_data = match.groupdict()
                view_name = parsed_data.get('viewName', '').replace('_', ' ')
                display_identifier = parsed_data.get('displaySpace', '')
                shaper_identifier = parsed_data.get('shaperSpace', '') if has_shaper_placeholder else None

                status = "OK"
                resolved_display_space = display_identifier # Default to identifier
                resolved_shaper = shaper_identifier # Default to identifier or None

                # Validate View Name
                if not view_name:
                    status = "Error: No View Name"
                else:
                    # Validate Display Space
                    display_obj = self._find_cs_by_name_or_shortname(display_identifier)
                    if not display_obj:
                        status = "Error: Invalid Display Space"
                        resolved_display_space = f"INVALID: {display_identifier}"
                    elif display_obj.category != 'display':
                         status = "Error: Not Display Category"
                         resolved_display_space = f"INVALID: {self._get_display_name(display_obj)}"
                    else:
                        resolved_display_space = self._get_display_name(display_obj)

                    # Validate Shaper Space (if required and status is still OK)
                    if status == "OK" and has_shaper_placeholder:
                        if not shaper_identifier:
                            status = "Error: No Shaper"
                            resolved_shaper = "MISSING"
                        else:
                            shaper_obj = self._find_cs_by_name_or_shortname(shaper_identifier)
                            is_valid_role = shaper_identifier in self.initial_roles

                            if not shaper_obj and not is_valid_role:
                                 status = "Error: Invalid Shaper"
                                 resolved_shaper = f"INVALID: {shaper_identifier}"
                            elif shaper_obj:
                                 if shaper_obj.encoding != 'log':
                                     status = "Error: Not Log Encoding"
                                     resolved_shaper = f"INVALID: {self._get_display_name(shaper_obj)}"
                                 else:
                                     resolved_shaper = self._get_display_name(shaper_obj)
                            elif is_valid_role:
                                 role_cs_name = self.initial_roles.get(shaper_identifier)
                                 role_cs_obj = self._find_cs_by_name_or_shortname(role_cs_name)
                                 # Validate against the *current* state of the roles tree
                                 role_cs_name = None
                                 role_cs_obj = None
                                 if self.roles_tree and self.roles_tree.exists(shaper_identifier):
                                     try:
                                         role_values = self.roles_tree.item(shaper_identifier, 'values')
                                         if len(role_values) > 1:
                                             assigned_cs_display = role_values[1]
                                             role_cs_name = self._get_underlying_cs_name(assigned_cs_display, resolve_role=False)
                                             if role_cs_name:
                                                 role_cs_obj = self._find_cs_by_name_or_shortname(role_cs_name)
                                     except tk.TclError:
                                         print(f"Warning: Could not get values for role '{shaper_identifier}' during LUT discovery.")

                                 if not role_cs_obj or role_cs_obj.encoding != 'log':
                                     status = "Error: Role not Log"
                                     resolved_shaper = f"INVALID_ROLE: {shaper_identifier}"
                                 else: # Role is valid and resolves to log
                                     resolved_shaper = shaper_identifier # Keep role name

                # Prepare data for matched pattern
                tags = ()
                if "Error" in status or "INVALID" in status or "MISSING" in status:
                    tags = ('error',)
                # Store data: ('LUT', filename, view_name, shaper, display_space, status, tags, original_filename)
                item_data = ('LUT', filename, view_name, resolved_shaper if resolved_shaper is not None else "", resolved_display_space, status, tags, filename)
                lut_data_to_display.append(item_data)

            else:
                # Pattern did not match - Add row for manual entry
                status = "Manual Entry Required"
                tags = ('manual',)
                # Store data: ('LUT', filename, "", "", "", status, tags, original_filename) - Still a LUT type
                item_data = ('LUT', filename, "", "", "", status, tags, filename)
                lut_data_to_display.append(item_data)


        # --- Apply Default View Mutate Rules ---
        # Store initial LUT views: { (display_fullname, view_name): {'shaper': ..., 'source_display_underlying': ...}, ... }
        initial_lut_views = {}
        for item_type, source, view, shaper, display, status, _, filename in lut_data_to_display:
            if item_type == 'LUT' and status == "OK": # Only consider valid LUTs as sources
                display_obj = self._find_cs_by_name_or_shortname(display)
                if display_obj:
                    display_fullname = display_obj.name
                    # Store the underlying name (short or long) of the source display
                    source_display_underlying = display_obj.shortname if display_obj.shortname else display_obj.name
                    initial_lut_views[(display_fullname, view)] = {'shaper': shaper, 'source_display_underlying': source_display_underlying, 'filename': filename}

        # Store existing views to avoid duplicate mutations: { (display_fullname, view_name) }
        existing_views = set(initial_lut_views.keys())

        # Load mutate rules from initial settings stored in the GUI
        view_mutate_rules = self.initial_settings.get('view_mutate', {})
        mutated_items_to_add = []

        for source_display_shortname, target_display_shortnames in view_mutate_rules.items():
            source_display_obj = self._find_cs_by_name_or_shortname(source_display_shortname)
            if not source_display_obj: continue
            source_display_fullname = source_display_obj.name
            # Get the underlying name (short or long) of the source display
            source_display_underlying = source_display_obj.shortname if source_display_obj.shortname else source_display_obj.name

            # Ensure target_display_shortnames is iterable, default to empty list if None
            for target_display_shortname in target_display_shortnames or []:
                target_display_obj = self._find_cs_by_name_or_shortname(target_display_shortname)
                if not target_display_obj: continue
                target_display_fullname = target_display_obj.name # Keep full name for backend check
                target_display_name_gui = self._get_display_name(target_display_obj) # Name for GUI display

                # Check views from the source display
                for (disp_fullname, view_name), source_data in initial_lut_views.items():
                    if disp_fullname == source_display_fullname:
                        # Check if this view already exists for the target
                        if (target_display_fullname, view_name) not in existing_views:
                            # Add mutation if it doesn't exist
                            # source_view_cs_name = source_data['source_cs'] # No longer needed here
                            shaper_name = source_data['shaper']
                            source_display_underlying_from_lut = source_data['source_display_underlying'] # Get stored underlying name
                            status = "OK (Mutated Default)"
                            tags = ('mutated_default',)
                            # Update 'Source' column text
                            source_column_text = f"Mutated from {view_name} / {self._get_display_name(source_display_obj)}" # Use current display name of source
                            # Store data: ('Mutated', source_column_text, view_name, shaper, target_display_name_gui, status, tags, {'view_name': view_name, 'source_display_underlying': source_display_underlying_from_lut, 'target_display_fullname': target_display_fullname})
                            item_data = ('Mutated', source_column_text, view_name, shaper_name, target_display_name_gui, status, tags, {'view_name': view_name, 'source_display_underlying': source_display_underlying_from_lut, 'target_display_fullname': target_display_fullname})
                            mutated_items_to_add.append(item_data)
                            existing_views.add((target_display_fullname, view_name)) # Mark as existing now

        # Combine original LUT data and default mutated data
        lut_data_to_display.extend(mutated_items_to_add)

        # Alphabetical sort: Display Space (idx 4), View Name (idx 2), Type (idx 0)
        lut_data_to_display.sort(key=lambda item: (item[4].lower(), item[2].lower(), item[0]))

        # --- Insert sorted data into Treeview ---
        for item_data in lut_data_to_display:
            item_type, source, view_name, resolved_shaper, resolved_display_space, status, tags, extra_data = item_data
            values = (item_type, source, view_name, resolved_shaper, resolved_display_space, status)
            item_id = self.lut_tree.insert('', tk.END, values=values, tags=tags)
            # Store internal data associated with the item
            if item_type == 'LUT':
                self.treeview_item_data[item_id] = {'type': 'LUT', 'filename': extra_data}
            elif item_type == 'Mutated':
                # Store the dict passed as extra_data directly
                self.treeview_item_data[item_id] = {'type': 'Mutated', **extra_data}


        # Configure tag styles
        self.lut_tree.tag_configure('error', foreground=DARK_ERROR_FG)
        self.lut_tree.tag_configure('manual', foreground=DARK_MANUAL_FG)
        self.lut_tree.tag_configure('mutated_default', foreground=DARK_DISABLED_FG) # Style for default mutations (e.g., gray)

        # Adjust column widths after populating
        self._adjust_treeview_column_widths(self.lut_tree)

        self.status_var.set(f"Found {lut_count} LUTs. Pattern matched {pattern_matched_count}. Check 'Manual Entry Required' rows.")


    def _populate_roles_treeview(self):
        """Populates the Roles Treeview with initial roles and assigned colorspaces."""
        if not self.roles_tree: return # Guard against missing widget

        # Clear existing items
        for item in self.roles_tree.get_children():
            self.roles_tree.delete(item)

        # Populate from self.initial_roles (which is an OrderedDict)
        for role_name, assigned_cs_name in self.initial_roles.items():
            assigned_cs_display = ""
            if assigned_cs_name:
                cs_obj = self._find_cs_by_name_or_shortname(assigned_cs_name)
                if cs_obj:
                    assigned_cs_display = self._get_display_name(cs_obj)
                else:
                    # Handle case where initial role points to a non-existent CS
                    assigned_cs_display = f"INVALID: {assigned_cs_name}"
                    print(f"Warning: Initial role '{role_name}' refers to unknown colorspace '{assigned_cs_name}'.")

            values = (role_name, assigned_cs_display)
            # Use role_name as the item ID (iid) for easy lookup
            self.roles_tree.insert('', tk.END, iid=role_name, values=values)

        # Adjust column widths after populating
        self._adjust_treeview_column_widths(self.roles_tree)


    def _get_active_underlying_names(self):
        """Returns a set of underlying names (shortname or name) for currently selected items in the active_cs_listbox."""
        active_names = set()
        selected_indices = self.active_cs_listbox.curselection()
        for i in selected_indices:
            try:
                display_name = self.active_cs_listbox.get(i)
                # Use the robust underlying name getter
                underlying = self._get_underlying_cs_name(display_name, resolve_role=False)
                if underlying:
                    active_names.add(underlying)
            except tk.TclError:
                print(f"Warning: Could not get listbox item at index {i} while getting active names.")
        return active_names


    def _get_current_role_names(self):
        """Returns a list of current role names (iids) from the roles treeview."""
        if not self.roles_tree: return []
        return self.roles_tree.get_children() # iids are role names


    def _is_name_active(self, underlying_name):
        """Checks if a given underlying name (short or long) is currently active."""
        if not underlying_name: return False
        active_names = self._get_active_underlying_names()
        return underlying_name in active_names


    # --- Treeview Editing Logic ---

    def _on_treeview_double_click(self, event):
        """Handle double-click events on the Treeview for editing."""
        self._destroy_treeview_edit_widget() # Destroy any existing edit widget first

        item_id = self.lut_tree.identify_row(event.y)
        column_id = self.lut_tree.identify_column(event.x)

        if not item_id or not column_id:
            return # Clicked outside of a cell

        column_index = int(column_id.replace('#', '')) - 1
        column_name = self.lut_tree['columns'][column_index]

        editable_columns = ['view', 'shaper', 'display_space'] # Keep 'source' non-editable for now
        item_type = self.treeview_item_data.get(item_id, {}).get('type', 'LUT')

        # Prevent editing certain columns, especially for Mutated types
        if column_name == 'type' or column_name == 'source':
             return
        if item_type == 'Mutated' and column_name in ['view', 'shaper']: # Maybe allow editing display?
             messagebox.showinfo("Edit Info", "View Name and Shaper Space for mutated views are inherited from the source and cannot be edited directly.")
             return
        if column_name not in editable_columns:
            return

        x, y, width, height = self.lut_tree.bbox(item_id, column_id)
        current_value = self.lut_tree.item(item_id, 'values')[column_index]

        # Strip INVALID/MISSING prefixes for editing
        if isinstance(current_value, str) and current_value.startswith(("INVALID:", "INVALID_ROLE:")):
             current_value = current_value.split(":", 1)[1].strip()
        elif current_value == "MISSING":
             current_value = ""

        var = tk.StringVar(value=current_value)
        widget = None

        if column_name == 'view':
            widget = ttk.Entry(self.lut_tree, textvariable=var)
            # Add FocusOut binding to commit edit
            widget.bind("<FocusOut>", self._save_treeview_edit)
        elif column_name == 'shaper':
            widget = ttk.Combobox(self.lut_tree, textvariable=var, state='readonly')
            widget['values'] = self.log_and_role_names
            if current_value in self.log_and_role_names: widget.set(current_value)
            elif widget['values']: widget.set(widget['values'][0])
        elif column_name == 'display_space':
            widget = ttk.Combobox(self.lut_tree, textvariable=var, state='readonly')
            widget['values'] = self.display_cs_names
            if current_value in self.display_cs_names: widget.set(current_value)
            elif widget['values']: widget.set(widget['values'][0])

        if not widget: return # Should not happen

        widget.place(x=x, y=y, width=width, height=height)
        widget.focus_force()
        if isinstance(widget, ttk.Combobox):
             # Add a small delay before generating the Down event
             widget.after(10, lambda: widget.event_generate('<Down>'))

        self.treeview_edit_widget = widget
        self.treeview_edit_details = {'item_id': item_id, 'column_index': column_index, 'var': var}

        # Bind common events
        widget.bind("<Return>", self._save_treeview_edit)
        widget.bind("<Escape>", self._destroy_treeview_edit_widget)
        if isinstance(widget, ttk.Combobox):
            widget.bind("<<ComboboxSelected>>", self._save_treeview_edit)


    def _validate_treeview_row(self, item_id):
        """Validates the view, shaper, and display space for a given treeview row."""
        # active_cs_underlying_names = self._get_active_underlying_names() # No longer needed here
        # Ensure item exists before trying to get values
        if not self.lut_tree.exists(item_id):
            return False, "Error: Item not found"

        values = self.lut_tree.item(item_id, 'values')
        # Check if values tuple has expected length (robustness)
        # Now expects 6 columns: type, source, view, shaper, display_space, status
        if len(values) < 6:
             return False, "Error: Invalid row data length"

        # Indices adjusted for new columns
        view_name = values[2]
        shaper_display = values[3]
        display_space_display = values[4]
        current_status = values[5] # Status is now at index 5

        # 1. Check View Name
        if not view_name:
            return False, "Error: No View Name"

        # 2. Validate Display Space
        display_obj = self._find_cs_by_name_or_shortname(display_space_display)
        if not display_obj:
            return False, f"Error: Unknown Display Space ('{display_space_display}')"
        if display_obj.category != 'display':
            return False, f"Error: Not Display Category ('{display_space_display}')"
        # Check if display space is active
        display_underlying = display_obj.shortname if display_obj.shortname else display_obj.name
        if not self._is_name_active(display_underlying): # Use helper method
            return False, f"Error: Display Space Not Active ('{display_space_display}')"

        # 3. Validate Shaper Space
        if not shaper_display:
             # If status was 'Manual Entry Required', empty shaper is invalid.
             # Also check if pattern required it (more complex, maybe skip for now)
             if current_status == "Manual Entry Required":
                 return False, "Error: No Shaper"
             # If pattern didn't require it (e.g., status was OK initially), empty is fine.
             # This logic might need refinement based on how pattern requirement is tracked.
             # Assuming for now that if it wasn't Manual, empty is OK if pattern allowed.
        else:
            shaper_underlying = self._get_underlying_cs_name(shaper_display, resolve_role=True)
            if not shaper_underlying:
                return False, f"Error: Unknown Shaper ('{shaper_display}')"
            # Check if it resolves to a log space
            shaper_obj = self._find_cs_by_name_or_shortname(shaper_underlying)
            is_log = False
            if shaper_obj and shaper_obj.encoding == 'log':
                is_log = True
            elif shaper_underlying in self._get_current_role_names(): # Check if it's a current role name
                # Get assigned CS from the roles treeview
                role_cs_name = None
                role_cs_obj = None
                if self.roles_tree and self.roles_tree.exists(shaper_underlying):
                     try:
                         role_values = self.roles_tree.item(shaper_underlying, 'values')
                         if len(role_values) > 1:
                             assigned_cs_display = role_values[1]
                             role_cs_name = self._get_underlying_cs_name(assigned_cs_display, resolve_role=False)
                             if role_cs_name:
                                 role_cs_obj = self._find_cs_by_name_or_shortname(role_cs_name)
                     except tk.TclError:
                         print(f"Warning: Could not get values for role '{shaper_underlying}' during validation.")

                if role_cs_obj and role_cs_obj.encoding == 'log':
                    is_log = True
                    # Also check if the resolved role CS is active
                    role_cs_underlying = role_cs_obj.shortname if role_cs_obj.shortname else role_cs_obj.name
                    if not self._is_name_active(role_cs_underlying):
                         return False, f"Error: Shaper Role CS Not Active ('{shaper_display}' -> '{role_cs_underlying}')"
                else:
                     # Role exists but doesn't resolve to an active log space
                     is_log = False # Mark as not log for the error below

            if not is_log:
                return False, f"Error: Not Log Encoding ('{shaper_display}')"
            # Check if shaper space itself (if it was a colorspace, not a role) is active
            elif shaper_obj and not self._is_name_active(shaper_obj.shortname if shaper_obj.shortname else shaper_obj.name): # Use helper method
                 return False, f"Error: Shaper Space Not Active ('{shaper_display}')"

        return True, "OK" # All checks passed


    def _save_treeview_edit(self, event=None):
        """Save the edited value back to the Treeview item and re-validate the row."""
        if not self.treeview_edit_widget or not self.treeview_edit_details:
             return

        details = self.treeview_edit_details
        item_id = details['item_id']
        column_index = details['column_index']
        var = details['var']
        new_value = var.get()

        # Store widget before potentially destroying it
        widget_to_destroy = self.treeview_edit_widget
        self.treeview_edit_widget = None # Prevent re-entry via FocusOut if validation fails below
        self.treeview_edit_details = None

        try:
            if not self.lut_tree.exists(item_id):
                print("Info: Treeview item no longer exists during save.")
                return
            current_values = list(self.lut_tree.item(item_id, 'values'))
        except tk.TclError:
             print("Error: Treeview item not found during save.")
             return

        # Update the specific value that was edited
        current_values[column_index] = new_value
        # Update the treeview immediately with the edited value before validation
        self.lut_tree.item(item_id, values=tuple(current_values))

        # Re-validate the entire row after the edit
        is_row_valid, new_status = self._validate_treeview_row(item_id)

        # Update the status in the values list (status is now at index 5)
        current_values[5] = new_status

        # Update the treeview item again with the potentially changed status
        self.lut_tree.item(item_id, values=tuple(current_values))

        # Update tags based on the new validation result
        tags = list(self.lut_tree.item(item_id, 'tags'))
        if not is_row_valid:
            if 'error' not in tags: tags.append('error')
            if 'manual' in tags: tags.remove('manual') # Error overrides manual
            if 'mutated_user' in tags: tags.remove('mutated_user') # Invalid edit removes user mutation tag? Or keep? Let's remove for now.
            if 'mutated_default' in tags: tags.remove('mutated_default')
        else: # Row is valid
            if 'error' in tags: tags.remove('error')
            if 'manual' in tags: tags.remove('manual') # Valid edit removes manual tag
            # Keep mutated tags if they were there and row is now valid

        self.lut_tree.item(item_id, tags=tuple(tags))

        # Destroy the widget *after* all updates
        if widget_to_destroy and widget_to_destroy.winfo_exists():
            widget_to_destroy.destroy()


    def _update_view_transform_validation_for_role(self, role_name):
        """Re-validates view transform rows that use the specified role name as a shaper."""
        if not self.lut_tree: return
        print(f"Re-validating View Transforms using role: {role_name}") # Debug
        for item_id in self.lut_tree.get_children():
            try:
                values = self.lut_tree.item(item_id, 'values')
                # Indices: 0:type, 1:source, 2:view, 3:shaper, 4:display_space, 5:status
                if len(values) > 3 and values[3] == role_name: # Check if shaper matches the role name
                    # Re-validate this row
                    is_valid, new_status = self._validate_treeview_row(item_id)
                    current_values = list(values)
                    current_values[5] = new_status # Update status
                    tags = list(self.lut_tree.item(item_id, 'tags'))
                    # Update tags based on validation
                    if not is_valid:
                        if 'error' not in tags: tags.append('error')
                        if 'manual' in tags: tags.remove('manual')
                    else:
                        if 'error' in tags: tags.remove('error')
                        # Keep other tags like 'mutated_user', 'mutated_default'
                    self.lut_tree.item(item_id, values=tuple(current_values), tags=tuple(tags))
            except tk.TclError:
                print(f"Warning: Could not access item {item_id} during role validation update.")


    def _update_treeview_shaper_dropdowns(self):
        """Updates the list of available shapers in any active Combobox editor."""
        # Update the master list first
        self._update_filtered_lists()
        # If a shaper combobox is currently active in the LUT tree, update its values
        if self.treeview_edit_widget and isinstance(self.treeview_edit_widget, ttk.Combobox):
            if self.treeview_edit_details:
                 col_idx = self.treeview_edit_details['column_index']
                 col_name = self.lut_tree['columns'][col_idx]
                 if col_name == 'shaper':
                     current_val = self.treeview_edit_details['var'].get()
                     self.treeview_edit_widget['values'] = self.log_and_role_names
                     # Try to preserve selection
                     if current_val in self.log_and_role_names:
                         self.treeview_edit_widget.set(current_val)
                     elif self.log_and_role_names:
                         self.treeview_edit_widget.set(self.log_and_role_names[0])
                     else:
                         self.treeview_edit_widget.set("")


    def _destroy_treeview_edit_widget(self, event=None):
        """Destroy the temporary editing widget."""
        if self.treeview_edit_widget:
            widget_to_destroy = self.treeview_edit_widget
            self.treeview_edit_widget = None
            self.treeview_edit_details = None
            try:
                if widget_to_destroy.winfo_exists():
                    widget_to_destroy.destroy()
            except tk.TclError:
                pass # Widget already destroyed


    # --- Roles Treeview Editing Logic ---

    def _on_roles_tree_double_click(self, event):
        """Handle double-click events on the Roles Treeview for editing."""
        self._destroy_roles_tree_edit_widget() # Destroy any existing edit widget first

        item_id = self.roles_tree.identify_row(event.y)
        column_id = self.roles_tree.identify_column(event.x)

        if not item_id or not column_id:
            return # Clicked outside of a cell

        column_index = int(column_id.replace('#', '')) - 1
        column_name = self.roles_tree['columns'][column_index]

        editable_columns = ['role_name', 'assigned_cs']
        if column_name not in editable_columns:
            return

        x, y, width, height = self.roles_tree.bbox(item_id, column_id)
        current_value = self.roles_tree.item(item_id, 'values')[column_index]

        # Strip INVALID prefix if present (for assigned_cs)
        if column_name == 'assigned_cs' and isinstance(current_value, str) and current_value.startswith("INVALID:"):
             current_value = current_value.split(":", 1)[1].strip()

        var = tk.StringVar(value=current_value)
        widget = None

        if column_name == 'role_name':
            widget = ttk.Entry(self.roles_tree, textvariable=var)
            # Add FocusOut binding to commit edit
            widget.bind("<FocusOut>", self._save_roles_tree_edit)
        elif column_name == 'assigned_cs':
            widget = ttk.Combobox(self.roles_tree, textvariable=var, state='readonly')
            # Populate with all active colorspace display names
            widget['values'] = [""] + self.all_cs_names # Add empty option
            if current_value in widget['values']: widget.set(current_value)
            elif widget['values']: widget.set(widget['values'][0]) # Default to empty

        if not widget: return

        widget.place(x=x, y=y, width=width, height=height)
        widget.focus_force()
        if isinstance(widget, ttk.Combobox):
             widget.after(10, lambda: widget.event_generate('<Down>')) # Open dropdown

        self.roles_tree_edit_widget = widget
        self.roles_tree_edit_details = {'item_id': item_id, 'column_index': column_index, 'var': var, 'original_value': current_value}

        # Bind common events
        widget.bind("<Return>", self._save_roles_tree_edit)
        widget.bind("<Escape>", self._destroy_roles_tree_edit_widget)
        if isinstance(widget, ttk.Combobox):
            widget.bind("<<ComboboxSelected>>", self._save_roles_tree_edit)


    def _save_roles_tree_edit(self, event=None):
        """Save the edited value back to the Roles Treeview item."""
        if not self.roles_tree_edit_widget or not self.roles_tree_edit_details:
             return

        details = self.roles_tree_edit_details
        item_id = details['item_id'] # This is the original role name (iid)
        column_index = details['column_index']
        column_name = self.roles_tree['columns'][column_index]
        var = details['var']
        new_value = var.get().strip() # Strip whitespace
        original_value = details['original_value']

        # Store widget before potentially destroying it
        widget_to_destroy = self.roles_tree_edit_widget
        self.roles_tree_edit_widget = None # Prevent re-entry
        self.roles_tree_edit_details = None

        try:
            if not self.roles_tree.exists(item_id):
                print(f"Info: Roles Treeview item '{item_id}' no longer exists during save.")
                return
            current_values = list(self.roles_tree.item(item_id, 'values'))
        except tk.TclError:
             print(f"Error: Roles Treeview item '{item_id}' not found during save.")
             return

        # --- Handle Edit ---
        needs_update = True
        new_item_id = item_id # Assume iid doesn't change initially

        if column_name == 'role_name':
            if new_value == original_value:
                needs_update = False # No change
            elif not new_value:
                 messagebox.showerror("Invalid Role Name", "Role name cannot be empty.")
                 needs_update = False
            elif ' ' in new_value:
                 messagebox.showerror("Invalid Role Name", "Role names cannot contain spaces.")
                 needs_update = False
            elif self.roles_tree.exists(new_value): # Check if new name already exists (and isn't the original)
                 messagebox.showerror("Duplicate Role Name", f"The role '{new_value}' already exists.")
                 needs_update = False
            else:
                 # Update the value in the list and the item ID (iid)
                 current_values[column_index] = new_value
                 new_item_id = new_value
                 # We need to re-insert the item with the new ID
                 needs_update = False # Handled by re-insertion below

                 # Get index before deleting
                 index = self.roles_tree.index(item_id)
                 # Get selection state
                 selection = self.roles_tree.selection()
                 was_selected = item_id in selection

                 # Delete old item
                 self.roles_tree.delete(item_id)
                 # Insert new item at the same index
                 self.roles_tree.insert('', index, iid=new_item_id, values=tuple(current_values))

                 # Restore selection if needed
                 if was_selected:
                     self.roles_tree.selection_set(new_item_id)

                 # Update filtered lists that depend on role names
                 self._update_filtered_lists()
                 # Update View Transform tree shaper dropdowns if they used the old role name
                 self._update_treeview_shaper_dropdowns()


        elif column_name == 'assigned_cs':
            if new_value == original_value:
                needs_update = False # No change
            else:
                # Validate the selected colorspace (optional, but good practice)
                if new_value and not self._find_cs_by_name_or_shortname(new_value):
                     print(f"Warning: Assigned colorspace '{new_value}' for role '{item_id}' seems invalid, but allowing.")
                     # Or show an error: messagebox.showerror(...) return
                current_values[column_index] = new_value
                # Update View Transform tree validation status if shaper used this role
                self._update_view_transform_validation_for_role(item_id)


        # Update the item in the treeview if needed (only for assigned_cs changes now)
        if needs_update:
            self.roles_tree.item(item_id, values=tuple(current_values))

        # Destroy the widget *after* all updates
        if widget_to_destroy and widget_to_destroy.winfo_exists():
            widget_to_destroy.destroy()


    def _destroy_roles_tree_edit_widget(self, event=None):
        """Destroy the temporary editing widget for the Roles Treeview."""
        if self.roles_tree_edit_widget:
            widget_to_destroy = self.roles_tree_edit_widget
            self.roles_tree_edit_widget = None
            self.roles_tree_edit_details = None
            try:
                if widget_to_destroy.winfo_exists():
                    widget_to_destroy.destroy()
            except tk.TclError:
                pass # Widget already destroyed


    def _handle_roles_tree_click(self, event):
        """Handles single clicks on the roles treeview to potentially save/cancel active edit."""
        if self.roles_tree_edit_widget and self.roles_tree_edit_details:
            # Identify what was clicked
            clicked_item = self.roles_tree.identify_row(event.y)
            clicked_col_id = self.roles_tree.identify_column(event.x)
            clicked_col_idx = int(clicked_col_id.replace('#', '')) - 1 if clicked_col_id else -1

            # Get details of the cell being edited
            editing_item = self.roles_tree_edit_details['item_id']
            editing_col_idx = self.roles_tree_edit_details['column_index']

            # If the click was NOT on the exact cell being edited, treat it like FocusOut: save the edit.
            if not (clicked_item == editing_item and clicked_col_idx == editing_col_idx):
                 # Check if the widget being edited is an Entry (for Role Name)
                 if isinstance(self.roles_tree_edit_widget, ttk.Entry):
                     self._save_roles_tree_edit() # Save on click outside for Entry
                 else:
                     # For Combobox, clicking outside usually means selection is done or cancelled by user action
                     self._destroy_roles_tree_edit_widget()


    # --- Roles Treeview Drag-and-Drop Logic (Similar to LUT Treeview) ---

    def _on_roles_tree_drag_start(self, event):
        """Handle start of drag for Roles Treeview."""
        region = self.roles_tree.identify_region(event.x, event.y)
        if region not in ("cell", "tree"):
            self._roles_drag_data = {"items": [], "start_y": 0}
            return

        item_id = self.roles_tree.identify_row(event.y)
        if not item_id:
             self._roles_drag_data = {"items": [], "start_y": 0}
             return

        selected_items_before_click = self.roles_tree.selection()

        if item_id in selected_items_before_click:
            self._roles_drag_data = {"items": selected_items_before_click, "start_y": event.y}
            return "break"
        else:
            self._roles_drag_data = {"items": [], "start_y": 0}
            self.master.after_idle(self._record_roles_drag_start_data, event.y, item_id)


    def _record_roles_drag_start_data(self, start_y, clicked_item_id):
        """Helper function called via after_idle to record roles drag data."""
        if not self.roles_tree.winfo_exists(): return
        selected_items = self.roles_tree.selection()
        if clicked_item_id in selected_items:
             self._roles_drag_data = {"items": selected_items, "start_y": start_y}
        else:
             self._roles_drag_data = {"items": [], "start_y": 0}


    def _on_roles_tree_drag_motion(self, event):
        """Move the dragged role item(s) during motion."""
        items_to_move = self._roles_drag_data.get("items")
        if not items_to_move: return

        target_id = self.roles_tree.identify_row(event.y)

        if target_id:
            target_index = self.roles_tree.index(target_id)
            try:
                original_indices = {item: self.roles_tree.index(item) for item in items_to_move if self.roles_tree.exists(item)}
            except tk.TclError: return
            sorted_items_to_move = sorted(items_to_move, key=lambda item: original_indices.get(item, float('inf')))

            current_target_index = target_index
            for item_id in sorted_items_to_move:
                 if self.roles_tree.exists(item_id):
                     self.roles_tree.move(item_id, '', current_target_index)
                     current_target_index += 1
        else:
            try:
                original_indices = {item: self.roles_tree.index(item) for item in items_to_move if self.roles_tree.exists(item)}
            except tk.TclError: return
            sorted_items_to_move = sorted(items_to_move, key=lambda item: original_indices.get(item, float('inf')))
            for item_id in sorted_items_to_move:
                if self.roles_tree.exists(item_id):
                    self.roles_tree.move(item_id, '', tk.END)


    def _on_roles_tree_drag_drop(self, event):
        """Finalize the roles drag operation."""
        self._roles_drag_data = {"items": [], "start_y": 0}


    # --- End Roles Treeview Editing & Drag Logic ---


    # --- Roles Treeview Add/Delete ---

    def _add_role(self):
        """Adds a new role row to the Roles Treeview."""
        if not self.roles_tree: return

        # Prompt for the new role name
        new_role_name = simpledialog.askstring("New Role", "Enter the name for the new role:", parent=self.master)
        if not new_role_name:
            return # User cancelled or entered empty string

        # Basic validation: Check for spaces and uniqueness
        if ' ' in new_role_name:
             messagebox.showerror("Invalid Role Name", "Role names cannot contain spaces.")
             return
        if self.roles_tree.exists(new_role_name):
            messagebox.showerror("Duplicate Role Name", f"The role '{new_role_name}' already exists.")
            return

        # Add the new role with an empty assigned colorspace
        values = (new_role_name, "") # Empty assigned CS initially
        self.roles_tree.insert('', tk.END, iid=new_role_name, values=values)
        # Optionally scroll to the new item
        self.roles_tree.see(new_role_name)
        # Update filtered lists that might include roles (e.g., for shaper space dropdown)
        self._update_filtered_lists()


    def _delete_selected_roles(self, event=None):
        """Deletes the selected role(s) from the Roles Treeview."""
        if not self.roles_tree: return
        selected_items = self.roles_tree.selection()
        if not selected_items:
            messagebox.showwarning("Delete Role", "No roles selected to delete.")
            return

        # Confirmation
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(selected_items)} selected role(s)?"):
            return

        for item_id in selected_items:
            if self.roles_tree.exists(item_id):
                self.roles_tree.delete(item_id)

        # Update filtered lists that might include roles
        self._update_filtered_lists()


    # --- End Roles Treeview Add/Delete ---


    def _handle_tree_click(self, event):
        """Handles single clicks on the treeview to potentially save/cancel active edit."""
        if self.treeview_edit_widget and self.treeview_edit_details:
            # Identify what was clicked
            clicked_item = self.lut_tree.identify_row(event.y)
            clicked_col_id = self.lut_tree.identify_column(event.x)
            clicked_col_idx = int(clicked_col_id.replace('#', '')) - 1 if clicked_col_id else -1

            # Get details of the cell being edited
            editing_item = self.treeview_edit_details['item_id']
            editing_col_idx = self.treeview_edit_details['column_index']

            # If the click was NOT on the exact cell being edited, treat it like FocusOut: save the edit.
            if not (clicked_item == editing_item and clicked_col_idx == editing_col_idx):
                 # Check if the widget being edited is an Entry (for View Name)
                 if isinstance(self.treeview_edit_widget, ttk.Entry):
                     self._save_treeview_edit() # Save on click outside for Entry
                 else:
                     # For Combobox, clicking outside usually means selection is done or cancelled by user action
                     # Destroying without saving might be more intuitive here, unless a selection was made which triggers save.
                     self._destroy_treeview_edit_widget()


    # Helper method for Ctrl+A binding on Text widgets
    def _select_all_text(self, widget):
        widget.tag_add("sel", "1.0", "end")
        return "break" # Prevent default behavior


    def _browse_output_path(self):
        """Open directory browser for output directory."""
        current_path_setting = self.output_dir_var.get()
        initial_dir = os.path.expanduser("~") # Default to home

        # Try to resolve the current path setting to an existing directory
        if os.path.isdir(current_path_setting):
            initial_dir = current_path_setting
        elif os.path.isdir(os.path.dirname(current_path_setting)):
             initial_dir = os.path.dirname(current_path_setting)


        directory = filedialog.askdirectory(initialdir=initial_dir, title="Select Output Directory")
        if directory:
            # Always use the absolute path
            abs_path = os.path.abspath(directory)
            self.output_dir_var.set(abs_path)

    # --- Treeview Drag-and-Drop Logic ---

    def _on_treeview_drag_start(self, event):
        """Handle start of drag, preserving multi-selection if click is on selected item."""
        # Ensure the click is within the treeview content area
        region = self.lut_tree.identify_region(event.x, event.y)
        if region not in ("cell", "tree"):
            self._drag_data = {"items": [], "start_y": 0} # Reset if clicking outside rows
            return # Don't start drag if clicking outside rows

        item_id = self.lut_tree.identify_row(event.y)
        if not item_id: # Clicked outside any item
             self._drag_data = {"items": [], "start_y": 0}
             return

        # Check selection *before* default behavior might change it
        selected_items_before_click = self.lut_tree.selection()

        if item_id in selected_items_before_click:
            # Clicked on item already in selection: Start drag with current selection immediately
            self._drag_data = {"items": selected_items_before_click, "start_y": event.y}
            # print(f"Drag Start (preserving selection): Items {self._drag_data['items']}") # Debug
            return "break" # IMPORTANT: Prevent default selection change
        else:
            # Clicked on unselected item: Let default selection run, then record
            # Reset drag data for now, it will be set by _record_drag_start_data if needed
            self._drag_data = {"items": [], "start_y": 0}
            self.master.after_idle(self._record_drag_start_data, event.y, item_id)
            # DO NOT return "break" here - allow default selection processing

    def _record_drag_start_data(self, start_y, clicked_item_id):
        """Helper function called via after_idle to record drag data *after* selection updates."""
        # Check if the widget still exists (window might have closed)
        if not self.lut_tree.winfo_exists():
            return

        selected_items = self.lut_tree.selection()

        # If the originally clicked item is still part of the selection
        # (or became the sole selection), store the current selection for dragging.
        if clicked_item_id in selected_items:
             self._drag_data = {"items": selected_items, "start_y": start_y}
             # print(f"Drag Start Recorded: Items {self._drag_data['items']}") # Debug
        else:
             # This case might occur if the click somehow deselected the item immediately,
             # or if the click was on an unselected item and default behavior didn't select it.
             # Reset drag data to prevent accidental drags.
             self._drag_data = {"items": [], "start_y": 0}
             # print(f"Drag Start Aborted: Clicked item {clicked_item_id} not in final selection {selected_items}") # Debug

    def _on_treeview_drag_motion(self, event):
        """Move the dragged item(s) during motion for live feedback."""
        items_to_move = self._drag_data.get("items")
        if not items_to_move:
            return # No drag in progress

        # Identify the target row under the current cursor position
        target_id = self.lut_tree.identify_row(event.y)

        if target_id:
            target_index = self.lut_tree.index(target_id)
            # Move the selected items to the target index
            # Get original indices *before* moving anything to sort correctly
            try:
                original_indices = {item: self.lut_tree.index(item) for item in items_to_move if self.lut_tree.exists(item)}
            except tk.TclError:
                 print("Warning: Error getting original indices during drag motion.")
                 return # Avoid errors if items disappear mid-drag

            # Sort items to move based on their original index to maintain relative order
            sorted_items_to_move = sorted(items_to_move, key=lambda item: original_indices.get(item, float('inf'))) # Handle potential missing items

            # Move items one by one to the target index, incrementing the index
            # to maintain relative order of the selection.
            current_target_index = target_index
            for item_id in sorted_items_to_move:
                 # Check if item still exists before moving
                 if self.lut_tree.exists(item_id):
                     # print(f"Moving {item_id} to index {current_target_index}") # Debug
                     self.lut_tree.move(item_id, '', current_target_index)
                     # Increment the target index for the *next* item in the selection
                     # This ensures subsequent selected items are placed sequentially *after* the current one.
                     current_target_index += 1

        else:
            # Cursor is outside any valid row (likely below the last item)
            # Move to the end of the list
            try:
                original_indices = {item: self.lut_tree.index(item) for item in items_to_move if self.lut_tree.exists(item)}
            except tk.TclError:
                 print("Warning: Error getting original indices during drag motion (end).")
                 return

            sorted_items_to_move = sorted(items_to_move, key=lambda item: original_indices.get(item, float('inf')))
            for item_id in sorted_items_to_move:
                if self.lut_tree.exists(item_id):
                    # print(f"Moving {item_id} to end") # Debug
                    self.lut_tree.move(item_id, '', tk.END)

    def _on_treeview_drag_drop(self, event):
        """Finalize the drag operation by resetting the state."""
        # The actual moving now happens in _on_treeview_drag_motion
        # This method just cleans up the drag state.
        # print("Drag Drop: Resetting state") # Debug
        self._drag_data = {"items": [], "start_y": 0}

    def _adjust_treeview_column_widths(self, tree):
        """Adjust column widths of the Treeview to fit content."""
        # Try to get the font used by the Treeview heading and cells
        try:
            style = ttk.Style()
            # Font for heading (might be different from cells)
            heading_font_str = style.lookup('Treeview.Heading', 'font')
            # Font for cells (Treeview style itself)
            cell_font_str = style.lookup('Treeview', 'font')

            # Create font objects
            heading_font = tkFont.Font(font=heading_font_str) if heading_font_str else tkFont.nametofont("TkDefaultFont")
            cell_font = tkFont.Font(font=cell_font_str) if cell_font_str else tkFont.nametofont("TkDefaultFont")

        except tk.TclError:
            # Fallback if style lookup fails
            print("Warning: Could not determine Treeview font from style. Using default font for width calculation.")
            heading_font = tkFont.nametofont("TkDefaultFont")
            cell_font = tkFont.nametofont("TkDefaultFont")

        padding = 20 # Add some padding for visual clarity

        for col_id in tree['columns']:
            # Measure heading width
            heading_text = tree.heading(col_id, 'text')
            max_width = heading_font.measure(heading_text)

            # Measure cell content width
            col_index = tree['columns'].index(col_id)
            for item_id in tree.get_children():
                 try:
                     values = tree.item(item_id, 'values')
                     # Ensure values tuple is long enough before accessing index
                     if col_index < len(values):
                         cell_text = str(values[col_index]) # Ensure string conversion
                         cell_width = cell_font.measure(cell_text)
                         max_width = max(max_width, cell_width)
                     else:
                         # Handle cases where a row might have fewer values than expected (shouldn't happen ideally)
                         print(f"Warning: Row {item_id} has fewer values than expected for column {col_id}.")
                 except tk.TclError:
                     # Item might have been deleted during iteration (unlikely but possible)
                     print(f"Warning: Could not access item {item_id} while calculating width for column {col_id}.")
                     continue # Skip this item

            # Set the column width with padding
            # Ensure minimum width to prevent columns from becoming too narrow if content is empty
            min_width = 50
            tree.column(col_id, width=max(min_width, max_width + padding), anchor='w') # Keep anchor='w'


    # --- End Treeview Drag-and-Drop Logic ---

    # --- End Treeview Editing Logic ---


    def _generate_config(self):
        """Gather data from GUI and trigger OCIO config generation."""
        self._destroy_treeview_edit_widget() # Ensure no lingering edit widgets

        self.status_var.set("Gathering settings...")
        print("Generate Config button clicked!")

        # --- Gather Data ---
        updated_settings = {
            "config_name": self.config_name_var.get(),
            "ocio_version_major": self.ocio_version_var.get(),
            "use_shortnames": self.use_shortnames_var.get(),
            "enable_descriptions": self.enable_descriptions_var.get(),
            "verbose_descriptions": self.verbose_descriptions_var.get(),
            "enable_builtins": self.enable_builtins_var.get(),
            "enable_colorspace_encoding": self.enable_encoding_var.get(),
            "enable_colorspace_aliases": self.enable_aliases_var.get(),
            "spi1d_lut_precision": self.spi1d_precision_var.get(),
            "category_folder_names": [{k: v.get()} for k, v in self.category_folder_vars.items()],
            "view_transform_settings": {
                "lut_search_path": self.lut_search_path_var.get(),
                "lut_filename_pattern": self.lut_pattern_var.get()
            },
            # Resolve reference colorspace *before* adding to settings
            "reference_log_colorspace": self.initial_settings.get('reference_log_colorspace'), # Use initial setting
            # Get description from Text widget (strip trailing newline)
            "config_description": self.config_description_text_widget.get("1.0", tk.END).strip() if self.config_description_text_widget else "",
            # --- Add view_mutate rules from initial load ---
            "view_mutate": self.initial_settings.get('view_mutate', {}) # Use initial setting
        }

        # --- Validate Reference Colorspace ---
        resolved_ref_cs = self._get_underlying_cs_name(self.ref_cs_var.get(), resolve_role=False)
        if not resolved_ref_cs:
            self.status_var.set("Error: Invalid or missing Reference Colorspace selection.")
            messagebox.showerror("Validation Error", "Please select a valid Reference Colorspace (Scene-Linear) in the 'Colorspaces & Roles' tab.")
            return # Stop generation
        updated_settings["reference_colorspace"] = resolved_ref_cs # Add validated name to settings

        # --- Gather Roles from Treeview (maintaining order) ---
        updated_roles = OrderedDict()
        if self.roles_tree:
            for item_id in self.roles_tree.get_children(): # Iterates in current display order
                try:
                    role_name = item_id # iid is the role name
                    values = self.roles_tree.item(item_id, 'values')
                    if len(values) > 1:
                        assigned_cs_display = values[1]
                        # Resolve display name to underlying name/shortname
                        underlying_name = self._get_underlying_cs_name(assigned_cs_display, resolve_role=False)
                        updated_roles[role_name] = underlying_name if underlying_name else ""
                    else:
                        updated_roles[role_name] = "" # Handle rows with missing values
                except tk.TclError:
                    print(f"Warning: Could not read role data for item '{item_id}' during generation.")
        else:
             self.status_var.set("Error: Roles Treeview not found.")
             messagebox.showerror("Internal Error", "Roles Treeview component is missing.")
             return

        # --- Gather Active Colorspaces ---
        selected_indices = self.active_cs_listbox.curselection()
        updated_active_cs = []
        for i in selected_indices:
            display_name = self.active_cs_listbox.get(i)
            underlying_name = self._get_underlying_cs_name(display_name, resolve_role=False)
            if underlying_name:
                updated_active_cs.append(underlying_name)

        # --- Gather View Transform data from Treeview (LUTs and Explicit Mutations) ---
        processed_vt_data = [] # For LUT-based views
        explicit_mutations = [] # For mutated views present in the GUI
        skipped_entries = []
        # Resolve LUT base path relative to CWD if not absolute
        lut_base_path = self.lut_search_path_var.get()
        if not os.path.isabs(lut_base_path):
             lut_base_path = os.path.abspath(os.path.join(os.getcwd(), lut_base_path))

        print("Validating and gathering View Transform entries from GUI...")
        for item_id in self.lut_tree.get_children():
            item_info = self.treeview_item_data.get(item_id)
            if not item_info:
                print(f"Warning: Missing internal data for tree item {item_id}. Skipping.")
                skipped_entries.append(f"Item {item_id} (Missing internal data)")
                continue

            values = self.lut_tree.item(item_id, 'values')
            # Indices: 0:type, 1:source, 2:view, 3:shaper, 4:display_space, 5:status
            item_type = values[0]
            source_val = values[1] # Filename or Source CS Name
            view_name = values[2]
            shaper_display = values[3]
            display_space_display = values[4]
            status = values[5]

            # Validate the row first (regardless of type)
            is_row_valid, validation_status = self._validate_treeview_row(item_id)
            if not is_row_valid:
                entry_desc = f"'{source_val}' -> '{view_name}'/'{display_space_display}'"
                print(f"Skipping invalid entry {entry_desc}: {validation_status}")
                skipped_entries.append(f"{entry_desc} ({validation_status})")
                # Update status in treeview if needed
                if status != validation_status:
                     current_values = list(values)
                     current_values[5] = validation_status # Status is at index 5 now
                     self.lut_tree.item(item_id, values=tuple(current_values), tags=('error',))
                continue

            # Process based on type
            if item_type == 'LUT':
                filename = item_info.get('filename')
                if not filename:
                     print(f"Internal Error: LUT item {item_id} missing filename in internal data. Skipping.")
                     skipped_entries.append(f"Item {item_id} (Missing filename)")
                     continue

                shaper_underlying = self._get_underlying_cs_name(shaper_display, resolve_role=True) if shaper_display else None
                display_underlying_obj = self._find_cs_by_name_or_shortname(display_space_display)
                if not display_underlying_obj: # Should be caught by validation, but safety check
                     print(f"Internal Error: Skipping LUT '{filename}' due to unresolved display space '{display_space_display}'.")
                     skipped_entries.append(f"{filename} (Internal display resolve error)")
                     continue

                display_full_name = display_underlying_obj.name
                processed_vt_data.append({
                    'lutFilename': filename,
                    'viewName': view_name,
                    'shaperSpace': shaper_underlying,
                    'displaySpace': display_full_name, # Pass full name to ociogen
                    'originalPath': os.path.join(lut_base_path, filename)
                })
            elif item_type == 'Mutated':
                # Retrieve stored components
                view_name = item_info.get('view_name')
                source_display_underlying = item_info.get('source_display_underlying')
                target_display_fullname = item_info.get('target_display_fullname') # Get target full name stored earlier

                # Find the source display object using the stored underlying name
                source_display_obj = self._find_cs_by_name_or_shortname(source_display_underlying)

                # Find the target display object (needed for validation, though already validated)
                target_display_obj = self._find_cs_by_name_or_shortname(display_space_display) # display_space_display is from treeview values

                if not view_name or not source_display_underlying or not target_display_fullname or not source_display_obj or not target_display_obj:
                     print(f"Internal Error: Mutated item {item_id} missing required data (view:'{view_name}', src_display:'{source_display_underlying}', target_display:'{target_display_fullname}') or objects not found. Skipping.")
                     skipped_entries.append(f"Mutated View '{view_name}' (Missing internal data/objects)")
                     continue

                # Construct names needed for backend *at generation time*
                source_display_name_for_transform = self._get_display_name(source_display_obj) # Respects current shortname toggle
                source_view_cs_name = f"{view_name} - {source_display_name_for_transform}" # Construct full source view name

                # Add tuple: (source_view_cs_name, source_display_name_for_transform, target_display_fullname, view_name)
                explicit_mutations.append((source_view_cs_name, source_display_name_for_transform, target_display_fullname, view_name))
            else:
                print(f"Warning: Unknown item type '{item_type}' for item {item_id}. Skipping.")
                skipped_entries.append(f"Item {item_id} (Unknown type: {item_type})")

        # --- Prepare Data for OCIOConfig ---
        config_data_for_init = {
            'settings': updated_settings,
            'roles': updated_roles,
            'active_colorspaces': updated_active_cs,
            'colorspaces': self.raw_colorspace_definitions
        }

        # --- Execute Generation ---
        self.status_var.set("Generating config...")
        log_stream = io.StringIO()
        success = False
        generated_path = None
        try:
            print("Instantiating OCIOConfig with GUI data...")
            output_dir = self.output_dir_var.get() # Get output dir from GUI
            # Pass the collected data using the 'initial_data' parameter
            ocio_generator = OCIOConfig(initial_data=config_data_for_init, output_dir=output_dir)

            print("Calling create_config...")
            with contextlib.redirect_stdout(log_stream), contextlib.redirect_stderr(log_stream):
                 # Pass both LUT data and explicit mutations to the backend
                 ocio_generator.create_config(view_transform_data=processed_vt_data, explicit_mutations=explicit_mutations)
            generated_path = ocio_generator.config_path
            success = True
            print("Config generation process completed.")

        except Exception as e:
            print(f"Error during generation: {e}")
            log_stream.write(f"\n\n*** ERROR DURING GENERATION ***\n{e}\n")
            success = False

        log_output = log_stream.getvalue()
        print(log_output)

        # --- Update Status ---
        if success and generated_path:
            final_message = f"Config generated successfully: {generated_path}"
            if skipped_entries: # Use the new list name
                final_message += f"\nSkipped {len(skipped_entries)} invalid/incomplete View Transform entries (see console log)."
                print("\n--- Skipped View Transform Entries ---")
                for skipped in skipped_entries: # Use the new list name
                    print(f"- {skipped}")
                print("-------------------------------------\n")
            self.status_var.set(final_message.split('\n')[0]) # Show main message in status bar
            messagebox.showinfo("Success", final_message)
        else:
            self.status_var.set("Config generation failed. Check console/log.")
            error_details = log_output if log_output else "Unknown error during generation."
            max_len = 1000
            if len(error_details) > max_len:
                error_details = error_details[:max_len] + "\n\n[Log truncated... Check console for full details]"
            messagebox.showerror("Generation Failed", f"Failed to generate OCIO configuration.\n\nDetails:\n{error_details}")


    def _toggle_theme(self):
        """Applies the selected theme (dark or light)."""
        if self.dark_mode_var.get():
            apply_dark_theme(self.master)
            # Update Text widget colors explicitly if needed
            if self.config_description_text_widget:
                self.config_description_text_widget.config(background=DARK_WIDGET_BG, foreground=DARK_FG,
                                                        insertbackground=DARK_INSERT_BG,
                                                        selectbackground=DARK_SELECT_BG,
                                                        selectforeground=DARK_SELECT_FG)
            # Update Listbox colors explicitly
            self.active_cs_listbox.config(background=DARK_WIDGET_BG, foreground=DARK_FG,
                                          selectbackground=DARK_SELECT_BG,
                                          selectforeground=DARK_SELECT_FG)
        else:
            apply_light_theme(self.master)
            # Update Text widget colors explicitly for light mode using defined constants
            if self.config_description_text_widget:
                self.config_description_text_widget.config(background=LIGHT_WIDGET_BG, foreground=LIGHT_FG,
                                                        insertbackground=LIGHT_INSERT_BG,
                                                        selectbackground=LIGHT_SELECT_BG,
                                                        selectforeground=LIGHT_SELECT_FG)
            # Update Listbox colors explicitly for light mode
            self.active_cs_listbox.config(background=LIGHT_WIDGET_BG, foreground=LIGHT_FG,
                                          selectbackground=LIGHT_SELECT_BG,
                                          selectforeground=LIGHT_SELECT_FG)
        # Force an update to ensure theme changes are applied, especially on macOS.
        self.master.update_idletasks()

    def _get_underlying_cs_name(self, display_name, resolve_role=True):
        """Finds the original name or shortname, or role name corresponding to a display name. More robustly handles shortname toggling."""
        if not display_name: return None

        # 1. Check if it's a *current* role name first (if allowed)
        current_role_names = self._get_current_role_names()
        if resolve_role and display_name in current_role_names:
            return display_name # Return the role name itself

        # 2. Prioritize matching against stable name/shortname attributes directly
        for cs_obj in self.colorspace_objects:
            if cs_obj.name == display_name:
                # Found by full name, return underlying (prefer shortname if exists)
                return cs_obj.shortname if cs_obj.shortname else cs_obj.name
            if cs_obj.shortname and cs_obj.shortname == display_name:
                # Found by shortname, return shortname
                return cs_obj.shortname

        # 3. Fallback: Check against the *current* display name (handles toggled shortnames)
        for cs_obj in self.colorspace_objects:
            current_display_name = self._get_display_name(cs_obj)
            if current_display_name == display_name:
                # Found by current display name, return underlying (prefer shortname if exists)
                return cs_obj.shortname if cs_obj.shortname else cs_obj.name

        # 4. If still not found, return None
        # print(f"Warning: Could not find underlying name/role for display name '{display_name}'")
        return None

    # --- Treeview Context Menu Logic ---

    def _show_treeview_context_menu(self, event):
        """Display context menu on right-click in the Treeview."""
        # Identify the item under the cursor
        item_id = self.lut_tree.identify_row(event.y)
        if not item_id:
            return # Clicked outside of any item

        # Select the item under the cursor if not already selected
        # Also handle multi-selection: if clicked item is part of existing selection, keep it.
        current_selection = self.lut_tree.selection()
        if item_id not in current_selection:
            self.lut_tree.selection_set(item_id) # Select only the clicked item if it wasn't selected
            current_selection = (item_id,) # Update selection tuple

        # Create the context menu
        context_menu = tk.Menu(self.master, tearoff=0)

        # Determine capabilities based on selection
        can_mutate = False
        can_delete = False # Reset flag
        for sel_id in current_selection:
            item_data = self.treeview_item_data.get(sel_id, {})
            item_type = item_data.get('type', 'LUT')
            # Check if *any* selected item exists (LUT or Mutated) to enable delete
            if item_data:
                can_delete = True
            # Check specifically for valid LUTs to enable mutate
            if item_type == 'LUT':
                is_row_valid, _ = self._validate_treeview_row(sel_id)
                if is_row_valid:
                    can_mutate = True
            # No need for specific check for Mutated to enable delete anymore

        # Add menu items based on capabilities
        mutate_state = tk.NORMAL if can_mutate else tk.DISABLED
        delete_state = tk.NORMAL if can_delete else tk.DISABLED

        context_menu.add_command(label="Mutate Selected View(s)...", command=self._mutate_selected_view, state=mutate_state)
        context_menu.add_command(label="Delete Selected View(s)", command=self._delete_selected_view, state=delete_state)

        # Display the menu
        context_menu.tk_popup(event.x_root, event.y_root)

    def _mutate_selected_view(self): # Removed item_id argument
        """Handles the 'Mutate View...' context menu action for selected items."""
        selected_items = self.lut_tree.selection()
        if not selected_items:
             messagebox.showwarning("Mutation Warning", "No items selected.")
             return

        valid_lut_items_to_mutate = []
        for item_id in selected_items:
            item_info = self.treeview_item_data.get(item_id)
            if item_info and item_info.get('type') == 'LUT':
                is_row_valid, _ = self._validate_treeview_row(item_id)
                if is_row_valid:
                    valid_lut_items_to_mutate.append(item_id)

        if not valid_lut_items_to_mutate:
            messagebox.showerror("Error", "No valid LUT entries selected for mutation.")
            return

        # --- Prompt for Target Display (Once for all selected) ---
        dialog = tk.Toplevel(self.master)
        dialog.title("Select Target Display")
        dialog.transient(self.master)
        dialog.update_idletasks() # Ensure window is viewable before grab
        dialog.grab_set()
        dialog.geometry("300x100")

        ttk.Label(dialog, text="Select target display to mutate to:").pack(pady=5)
        target_display_var = tk.StringVar()
        # Get display names, potentially excluding source displays if desired (more complex)
        # For now, allow selecting any display space
        target_combo = ttk.Combobox(dialog, textvariable=target_display_var, values=self.display_cs_names, state='readonly')
        target_combo.pack(pady=5, padx=10, fill='x')
        if self.display_cs_names:
            target_combo.current(0)

        result = {"selected": None}
        def on_ok():
            result["selected"] = target_display_var.get()
            dialog.destroy()
        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ok_button = ttk.Button(button_frame, text="OK", command=on_ok, state=tk.NORMAL if self.display_cs_names else tk.DISABLED)
        ok_button.pack(side=tk.LEFT, padx=5)
        cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel)
        cancel_button.pack(side=tk.LEFT, padx=5)

        self.master.wait_window(dialog)
        target_display_gui = result["selected"]
        if not target_display_gui:
            return # User cancelled

        target_display_obj = self._find_cs_by_name_or_shortname(target_display_gui)
        if not target_display_obj:
             messagebox.showerror("Error", f"Could not find selected target display colorspace '{target_display_gui}'.")
             return
        target_display_fullname = target_display_obj.name # Keep full name for backend check
        # --- End Prompt ---

        mutations_added = 0
        mutations_skipped = 0
        for item_id in valid_lut_items_to_mutate:
            values = self.lut_tree.item(item_id, 'values')
            view_name = values[2]
            shaper_display = values[3]
            source_display_gui = values[4]

            # Prevent mutating to the same display
            if source_display_gui == target_display_gui:
                print(f"Skipping mutation for '{view_name}': Source and target display are the same ('{target_display_gui}').")
                mutations_skipped += 1
                continue

            source_display_obj = self._find_cs_by_name_or_shortname(source_display_gui) # Should exist due to validation
            # Get the underlying name (short or long) of the source display
            source_display_underlying = source_display_obj.shortname if source_display_obj.shortname else source_display_obj.name
            # source_display_fullname = source_display_obj.name # No longer needed here

            # Check if this mutation already exists based on view_name, source_display_underlying, and target_display_gui
            mutation_exists = False
            for existing_item_id in self.lut_tree.get_children():
                existing_data = self.treeview_item_data.get(existing_item_id, {})
                if existing_data.get('type') == 'Mutated':
                    existing_values = self.lut_tree.item(existing_item_id, 'values')
                    if (existing_data.get('view_name') == view_name and
                        existing_data.get('source_display_underlying') == source_display_underlying and
                        existing_values[4] == target_display_gui): # Check target display in tree
                        mutation_exists = True
                        break
            if mutation_exists:
                print(f"Skipping mutation for '{view_name}' to '{target_display_gui}': Already exists.")
                mutations_skipped += 1
                continue

            # Add new row
            status = "OK (Mutated User)"
            tags = ('mutated_user',)
            # Update 'Source' column text
            source_column_text = f"Mutated from {view_name} / {source_display_gui}"
            new_values = ('Mutated', source_column_text, view_name, shaper_display, target_display_gui, status)
            new_item_id = self.lut_tree.insert('', tk.END, values=new_values, tags=tags)
            # Store view_name and source_display_underlying
            self.treeview_item_data[new_item_id] = {'type': 'Mutated', 'view_name': view_name, 'source_display_underlying': source_display_underlying, 'target_display_fullname': target_display_fullname}
            mutations_added += 1

        if mutations_added > 0:
             messagebox.showinfo("Mutation Complete", f"Added {mutations_added} new view mutation(s) for display '{target_display_gui}'.")
        if mutations_skipped > 0:
             messagebox.showwarning("Mutation Skipped", f"Skipped {mutations_skipped} mutation(s) (already existed or source=target).")


    def _delete_selected_view(self, event=None): # Added event=None for key binding compatibility
        """Handles the 'Delete Selected View(s)' context menu action and Delete key press."""
        selected_items = self.lut_tree.selection()
        if not selected_items:
             messagebox.showwarning("Delete Warning", "No items selected.")
             return

        items_to_delete = []
        # Identify all selected items, regardless of type
        items_to_delete = list(selected_items)

        if not items_to_delete:
            messagebox.showwarning("Delete Warning", "No views selected for deletion.")
            return

        # Confirmation dialog - updated message
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(items_to_delete)} selected view(s)?\nThis cannot be undone."):
            return

        deleted_count = 0
        for item_id in items_to_delete:
            try:
                if item_id in self.treeview_item_data:
                    del self.treeview_item_data[item_id]
                self.lut_tree.delete(item_id)
                deleted_count += 1
            except tk.TclError as e:
                print(f"Error deleting treeview item {item_id}: {e}")

        if deleted_count > 0:
             print(f"Deleted {deleted_count} view(s).") # Simple console confirmation
        # No need for a popup confirmation anymore

    # --- End Treeview Context Menu Logic ---


__all__ = [
    "OCIOGenGUI",
    "Tooltip",
    "apply_dark_theme",
    "apply_light_theme"
]

def main():
    """Entry point for the GUI application."""

    def _initialize_tkinter() -> tk.Tk:
        # https://rye.astral.sh/guide/faq/#tkinter-support
        try:
            return tk.Tk()  # Initialize Tkinter to ensure Tcl/Tk is set up
        except tk.TclError:
            os.environ["TCL_LIBRARY"] = sys.base_prefix + "/lib/tcl8.6"
            os.environ["TK_LIBRARY"] = sys.base_prefix + "/lib/tk8.6"
            try:
                return tk.Tk()  # Try initializing again after setting the environment variables
            except tk.TclError as e:
                raise RuntimeError(
                    "Failed to initialize Tkinter. Ensure Tcl/Tk is installed correctly."
                ) from e

    root = _initialize_tkinter()
    app = OCIOGenGUI(root)
    # Force the window to update before starting the main event loop.
    # This can fix issues on some platforms (like macOS) where the window
    # might not draw its contents correctly until the event loop is running.
    root.update_idletasks()
    root.mainloop()

if __name__ == "__main__":
    main()
