import os
import sys
import shutil
import PyOpenColorIO as ocio
import contextlib
import io
import itertools
import yaml
import re
from collections import OrderedDict
from pathlib import Path
import importlib.resources
from dataclasses import dataclass
from inspect import getmembers, isfunction

# Import necessary components from utilities
# Assuming utilities are in the same package level
from .utilities import transfer_functions
from .utilities.colorimetry import rgb_to_rgb, is_identity, pad_4x4

# --- Constants ---
VALID_LUT_EXTENSIONS = {'.cube', '.cub', '.spi3d', '.3dl', '.csp'}

# --- Dataclasses ---
@dataclass
class Colorspace:
    name: str # Colorspace name.
    category: object = None  # work, camera, display, image
    shortname: object = None # a short compressed version of the colorspace name
    alias: object = None # Alias for this colorspace (OCIO V2 only)
    description: str = '' # Colorspace description
    encoding: str = '' # Colorspace encoding: scene-linear, log, sdr-video, hdr-video, data (OCIO V2 only)
    chr: object = None # 1x8 list of RGBW xy chromaticities, or string for another colorspace
    tf: object = None # Colorspace transfer function: a python method or None if linear
    tf_builtin: object = None # OCIO Builtin function option (OCIO v2 only)
    forward: bool = True # forward is the TO_REFERENCE direction, otherwise FROM_REFERENCE


# --- Core Logic Class ---
class OCIOConfig:
    # Note: Removed config_data argument as it's GUI specific and core shouldn't depend on GUI structure
    def __init__(self, config_settings_path=None, output_dir=None):
        """
        Initialize OCIOConfig.
        Loads configuration settings based on the provided path or defaults.
        Loads colorspace definitions *always* from package data.
        output_dir specifies the parent directory for the generated config folder.
        """
        settings_source = None # Variable to hold the dictionary containing settings

        settings_data = None # To store data from config.yaml
        colorspace_list_data = None # To store data from colorspaces.yaml

        # --- Determine Config Settings Source ---
        config_load_source_msg = "" # Message indicating where settings were loaded from

        if config_settings_path:
            # Custom path provided via CLI
            abs_config_path = Path(os.path.abspath(config_settings_path))
            if not abs_config_path.is_file():
                print(f"Error: Custom config file not found at '{abs_config_path}'. Exiting.")
                sys.exit(1)
            try:
                with open(abs_config_path, 'r', encoding='utf-8') as f_settings:
                    settings_data = yaml.safe_load(f_settings)
                config_load_source_msg = f"Loading config settings from custom path: {abs_config_path}"
            except Exception as e:
                print(f"Error loading custom config settings from '{abs_config_path}': {e}")
                sys.exit(1)
        else:
            # No custom path, check CWD
            local_config_path = Path(os.getcwd()) / 'config.yaml' # Look for config.yaml in CWD
            if local_config_path.is_file():
                try:
                    with open(local_config_path, 'r', encoding='utf-8') as f_settings:
                        settings_data = yaml.safe_load(f_settings)
                    config_load_source_msg = f"Loading config settings from local file: {local_config_path}"
                except Exception as e:
                    print(f"Error loading local config settings from '{local_config_path}': {e}")
                    sys.exit(1)
            else:
                # Fallback to package data
                try:
                    data_pkg_ref = importlib.resources.files('ociogen.data')
                    config_path_ref = data_pkg_ref.joinpath('config.yaml')
                    with config_path_ref.open('r', encoding='utf-8') as f_settings:
                        settings_data = yaml.safe_load(f_settings)
                    config_load_source_msg = "Loading default config settings from package data."
                except FileNotFoundError as e:
                    print(f"Error: Default configuration file 'config.yaml' not found in package data: {e.filename}")
                    sys.exit(1)
                except Exception as e:
                    print(f"Error loading default config settings from package data: {e}")
                    sys.exit(1)

        print(config_load_source_msg)

        # --- Load Colorspaces (Always from Package Data) ---
        try:
            data_pkg_ref = importlib.resources.files('ociogen.data')
            colorspaces_path_ref = data_pkg_ref.joinpath('colorspaces.yaml')
            with colorspaces_path_ref.open('r', encoding='utf-8') as f_colorspaces:
                colorspace_list_data = yaml.safe_load(f_colorspaces)
            print("Loading colorspace definitions from package data.")
        except FileNotFoundError as e:
            print(f"Error: Default colorspace file 'colorspaces.yaml' not found in package data: {e.filename}")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading default colorspace definitions from package data: {e}")
            sys.exit(1)

        # Now, extract 'settings', 'roles', etc. from the loaded settings_data
        if settings_data:
             self.settings = settings_data.get('settings', {}) # Get the 'settings' dict
             # Check if settings were actually found
             if not self.settings:
                  print("Error: 'settings' section not found in the configuration file.")
                  sys.exit(1)
             # Extract other top-level keys from settings_data
             self.roles = settings_data.get('roles', {})
             self.active_colorspaces = settings_data.get('active_colorspaces')
             # colorspace_list_data is already loaded separately above
        else:
             # This case should be handled by the file loading error check above
             print("Error: Failed to load settings data.")
             sys.exit(1)

        # Validate that colorspace_list_data was loaded
        if colorspace_list_data is None:
            print("Error: Failed to load colorspace data from colorspaces.yaml.")
            sys.exit(1)

        # --- Validate Essential Settings Early ---
        # Check for reference_colorspace immediately after loading settings
        ref_cs_name = self.settings.get('reference_colorspace')
        if not ref_cs_name:
            print("Error: 'reference_colorspace' must be defined in the settings section of the configuration.")
            sys.exit(1)
        # We will validate if this name maps to an actual colorspace later,
        # after colorspaces are loaded.

        self.config = ocio.Config()
        self.ocio_version_major = self.settings.get('ocio_version_major')
        if self.ocio_version_major is None:
            print("Warning: 'ocio_version_major' not set in settings. Defaulting to 1.")
            self.ocio_version_major = 1

        if self.active_colorspaces is None:
             print("Warning: 'active_colorspaces' not defined in configuration source. All colorspaces will be considered active.")
             self.active_colorspaces = [] # Or handle differently if needed

        # --- Load Colorspace Definitions ---
        if not isinstance(colorspace_list_data, list):
             print("Error: colorspaces.yaml did not resolve to a list.")
             sys.exit(1) # Exit if colorspaces aren't a list

        # Populate self.colorspaces from the extracted list data
        self.colorspaces = list()
        self._get_colorspaces(colorspace_list_data)

        # Determine output directory
        self.output_dir = output_dir # Use provided output_dir if available
        if not self.output_dir:
            # Fallback to settings in config.yaml if not provided directly
            config_location = self.settings.get("config_location", "~/Desktop") # Default to Desktop if not in settings
            self.output_dir = os.path.expanduser(config_location)
        else:
            # Ensure provided output_dir is absolute and expanded
            self.output_dir = os.path.abspath(os.path.expanduser(self.output_dir))

        print(f"Output directory set to: {self.output_dir}")

        # Get reference colorspace name (already checked for existence)
        ref_cs_name = self.settings.get('reference_colorspace')
        # Now, validate that the name corresponds to a loaded colorspace
        self.reference_colorspace = self._get_colorspace_from_name(ref_cs_name)
        if not self.reference_colorspace:
            print(f"Error: Defined reference_colorspace '{ref_cs_name}' not found in the loaded colorspaces.")
            sys.exit(1)

        # Set spi1d LUT size
        spi1d_lut_precision = self.settings.get('spi1d_lut_precision')
        if spi1d_lut_precision:
            try:
                self.LUT_SIZE = int(2**spi1d_lut_precision)
            except (ValueError, TypeError):
                print(f"Warning: Invalid 'spi1d_lut_precision' value '{spi1d_lut_precision}'. Defaulting to 13 (8192).")
                self.LUT_SIZE = int(2**13)
        else:
            self.LUT_SIZE = int(2**13)

        # set allocation vars
        self.allocation_vars = [-8, 8, 0.01]

        # Prepare for view transform generation
        self.generated_view_transform_colorspaces = [] # Stores generated OCIO colorspace objects
        self.ocio_displays_structure = {} # Stores the final structure for the 'displays' section
        self.view_mutate_rules = self.settings.get('view_mutate', {}) # Load view_mutate rules


    def _snake_to_camel(self, snake_str):
        """Converts snake_case string to camelCase"""
        components = snake_str.split('_')
        # We capitalize the first letter of each component except the first one
        # with the 'title' method and join them together.
        return components[0] + ''.join(x.title() for x in components[1:])

    def _get_colorspaces(self, colorspace_data):
        ''' Populate self.colorspaces (list) with the data in the colorspaces list
        '''

        # Assemble dict of all transfer function methods from transfer_functions module
        tfuncs = {}
        for nm, fn in getmembers(transfer_functions, isfunction):
            tfuncs[nm] = fn

        for cs_def in colorspace_data:
            # Check if colorspace should be active (only if active_colorspaces list is defined)
            shortname = cs_def.get('shortname')
            if self.active_colorspaces and shortname not in self.active_colorspaces:
                continue # Skip inactive colorspaces
            elif not shortname:
                print(f"Warning: Colorspace '{cs_def.get('name', 'Unnamed')}' has no shortname! Cannot check if active.")
                # Decide whether to include it or skip it if no shortname
                # continue # Option: skip if no shortname

            # Make a copy to avoid modifying the original loaded data if needed elsewhere
            cs = cs_def.copy()

            # --- Transfer Function Logic ---
            python_tf_function = None # Store the resolved Python function here
            tf_str = cs.get('tf')
            if tf_str:
                if tf_str in tfuncs:
                    python_tf_function = tfuncs.get(tf_str)
                else:
                    print(f"Warning: Transfer function '{tf_str}' for colorspace '{cs.get('name')}' not found in utilities.transfer_functions.")
                    # python_tf_function remains None

            # --- Builtin Transform Logic ---
            builtin_transform = None # Store the potential OCIO builtin transform here
            tf_builtin_value = cs.get('tf_builtin')
            if tf_builtin_value:
                if isinstance(tf_builtin_value, dict):
                    builtin_type = tf_builtin_value.get('type')
                    builtin_params = tf_builtin_value.get('params', {})
                    camel_case_params = {self._snake_to_camel(k): v for k, v in builtin_params.items()}
                    temp_transform = None # Use a temporary variable inside the try block
                    try:
                        # Check OCIO version compatibility
                        if builtin_type == 'LogCameraTransform':
                            if self.ocio_version_major > 1:
                                temp_transform = self._OCIO_LogCameraTransform(**camel_case_params)
                            # else:
                            #     print(f"Warning: Builtin transform type '{builtin_type}' requires OCIO v2+, but config is set to v{self.ocio_version_major}. Cannot use for colorspace '{cs.get('name')}'.")
                        elif builtin_type == 'LogAffineTransform':
                             if self.ocio_version_major > 1:
                                temp_transform = self._OCIO_LogAffineTransform(**camel_case_params)
                            #  else:
                            #     print(f"Warning: Builtin transform type '{builtin_type}' requires OCIO v2+, but config is set to v{self.ocio_version_major}. Cannot use for colorspace '{cs.get('name')}'.")
                        elif builtin_type == 'ExponentWithLinearTransform':
                            if self.ocio_version_major > 1:
                                temp_transform = self._OCIO_ExponentWithLinearTransform(**camel_case_params)
                            # else:
                            #     print(f"Warning: Builtin transform type '{builtin_type}' requires OCIO v2+, but config is set to v{self.ocio_version_major}. Cannot use for colorspace '{cs.get('name')}'.")
                        elif builtin_type == 'ExponentTransform': # Works in v1 and v2
                            temp_transform = self._OCIO_ExponentTransform(**camel_case_params)
                        elif builtin_type == 'BuiltinTransform':
                            if self.ocio_version_major > 1:
                                temp_transform = self._OCIO_BuiltinTransform(**camel_case_params)
                            # else:
                            #     print(f"Warning: Builtin transform type '{builtin_type}' requires OCIO v2+, but config is set to v{self.ocio_version_major}. Cannot use for colorspace '{cs.get('name')}'.")
                        else:
                            print(f"Warning: Unknown or unsupported tf_builtin type '{builtin_type}' for colorspace '{cs.get('name')}'")

                        if temp_transform:
                            builtin_transform = temp_transform # Assign to outer variable if successful

                    except TypeError as e:
                        print(f"Error creating builtin transform '{builtin_type}' for '{cs.get('name')}': {e}. Check parameters.")
                        # builtin_transform remains None
                    except ocio.Exception as e:
                        print(f"OCIO Error creating builtin transform '{builtin_type}' for '{cs.get('name')}': {e}. Check parameters.")
                        # builtin_transform remains None
                else:
                    print(f"Warning: Invalid format for tf_builtin (expected dict) for colorspace '{cs.get('name')}'")
                    # builtin_transform remains None


            # --- Final TF Selection ---
            final_tf = None
            use_builtin_override = self.settings.get('enable_builtins', False) # Default to False if missing

            if python_tf_function:
                if use_builtin_override and builtin_transform:
                    final_tf = builtin_transform # Override with builtin if enabled and available
                else:
                    final_tf = python_tf_function # Use Python function (default or if override disabled/builtin invalid)
            elif builtin_transform:
                final_tf = builtin_transform # Fallback to builtin if no Python function and builtin is valid
            # else: final_tf remains None

            cs['tf'] = final_tf # Assign the chosen transform (or None)

            # --- End of TF Logic ---

            # Convert chr list values to float if present
            if cs.get('chr'):
                if isinstance(cs['chr'], list):
                    try:
                        cs['chr'] = [float(x) for x in cs['chr']]
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Invalid chromaticity value in list for colorspace '{cs.get('name')}': {e}. Skipping chr.")
                        cs['chr'] = None
                elif not isinstance(cs['chr'], str):
                    print(f"Warning: Invalid type for 'chr' in colorspace '{cs.get('name')}' (expected list or string). Skipping chr.")
                    cs['chr'] = None


            # Create Colorspace object
            try:
                # Filter out keys not expected by the Colorspace dataclass constructor
                valid_keys = Colorspace.__annotations__.keys()
                filtered_cs_args = {k: v for k, v in cs.items() if k in valid_keys}
                colorspace_obj = Colorspace(**filtered_cs_args)
                self.colorspaces.append(colorspace_obj)
            except TypeError as e:
                print(f"Error creating Colorspace object for '{cs.get('name', 'Unnamed')}': {e}. Check definition.")


    def _get_colorspace_from_name(self, name):
        """Helper method to get colorspace object by name or shortname"""
        if not name: return None
        for c in self.colorspaces:
            # Check shortname first if use_shortnames is enabled
            if self.settings.get('use_shortnames') and c.shortname == name:
                return c
            # Then check full name
            if c.name == name:
                return c
            # If shortnames aren't used, check shortname as a fallback (might be ambiguous)
            if not self.settings.get('use_shortnames') and c.shortname == name:
                # print(f"Warning: Found colorspace by shortname '{name}' but use_shortnames is false. This might be ambiguous.")
                return c
        # If not found by primary identifiers, maybe it was intended as a shortname even if use_shortnames is false?
        # Or maybe it was intended as a full name even if use_shortnames is true? Check again.
        for c in self.colorspaces:
            if c.shortname == name or c.name == name:
                # print(f"Debug: Found '{name}' as secondary identifier for '{c.name}'/'{c.shortname}'")
                return c

        # print(f"Debug: Colorspace '{name}' not found.") # Reduced noise
        return None


    def _prompt_for_colorspace(self, lut_filename, required_type):
        """
        Prompts the user for a colorspace name or role when parsing fails.
        required_type: 'display' or 'shaper'
        Returns the validated, resolved colorspace name or None.
        """
        prompt_message = f"Could not automatically determine the '{required_type}' colorspace for LUT '{lut_filename}'.\n"
        if required_type == 'shaper':
            prompt_message += "Please enter the correct colorspace name or role for the shaper space (or leave blank to skip): "
        else: # display
            prompt_message += "Please enter the correct colorspace name for the display (or leave blank to skip): "

        while True:
            user_input = input(prompt_message).strip()
            if not user_input:
                print(f"Skipping LUT '{lut_filename}' due to missing {required_type} information.")
                return None # User chose to skip

            resolved_obj = self._get_colorspace_from_name(user_input)
            resolved_name = None

            if resolved_obj:
                # For display, always use the full name internally for the key
                # For shaper, use the name respecting use_shortnames
                resolved_name = resolved_obj.name if required_type == 'display' else self.get_cs_name(resolved_obj)
            elif required_type == 'shaper':
                # Check if it's a valid role that resolves to a colorspace
                role_resolved_name = self.roles.get(user_input)
                if role_resolved_name and self._get_colorspace_from_name(role_resolved_name):
                    resolved_name = role_resolved_name # Use the resolved name from the role

            if resolved_name:
                print(f"Using '{resolved_name}' as the {required_type} space for '{lut_filename}'.")
                return resolved_name # Valid input found
            else:
                print(f"Error: '{user_input}' is not a valid, active colorspace name or role. Please try again.")
                # Loop continues


    def _parse_lut_filename(self, lut_filename):
        """
        Parses a LUT filename based on the pattern in settings, ignoring the extension.
        Validates required components (view, display, shaper if applicable) and checks extension.
        Returns a dict with parsed info {'viewName': ..., 'displaySpace': ..., 'shaperSpace': ..., 'lutFilename': ...} or None if invalid extension or pattern mismatch.
        """
        # 1. Check Extension
        name_part, ext = os.path.splitext(lut_filename)
        if ext.lower() not in VALID_LUT_EXTENSIONS:
            # print(f"Debug: Skipping '{lut_filename}', invalid extension '{ext}'.")
            return None

        # 2. Get Pattern from Settings (now extensionless)
        settings = self.settings.get('view_transform_settings', {})
        filename_pattern = settings.get('lut_filename_pattern') # Expecting extensionless pattern
        if not filename_pattern:
            print(f"Warning: 'lut_filename_pattern' not found in view_transform_settings. Cannot parse '{lut_filename}'.")
            return None

        # --- 3. Build Regex from Pattern ---
        # Placeholders to look for
        placeholders = {
            'viewName': r'(?P<viewName>.+)',
            'displaySpace': r'(?P<displaySpace>.+)',
            'shaperSpace': r'(?P<shaperSpace>.+?)' # Non-greedy match for shaper
        }
        regex_pattern_str = re.escape(filename_pattern) # Escape the literal parts of the pattern

        # Replace escaped placeholders with regex capturing groups
        has_shaper_placeholder = False
        for key, regex_part in placeholders.items():
            placeholder_escaped = re.escape(f"{{{key}}}")
            if placeholder_escaped in regex_pattern_str:
                regex_pattern_str = regex_pattern_str.replace(placeholder_escaped, regex_part, 1)
                if key == 'shaperSpace':
                    has_shaper_placeholder = True

        # Anchor the regex to match the whole name_part
        regex_pattern_str = f"^{regex_pattern_str}$"

        # --- 4. Match Filename (Name Part Only) ---
        match = re.match(regex_pattern_str, name_part)
        if not match:
            # print(f"Debug: Filename part '{name_part}' did not match pattern regex '{regex_pattern_str}'")
            # This is now expected behavior for files to be added manually in the GUI
            return None # Return None if pattern doesn't match the name part

        parsed_data = match.groupdict()

        # --- 5. Validate Required Components ---
        if 'viewName' not in parsed_data or not parsed_data['viewName']:
            print(f"Warning: Could not parse 'viewName' from LUT filename '{lut_filename}' using pattern. Skipping.")
            return None
        parsed_data['viewName'] = parsed_data['viewName'].replace('_', ' ') # Replace underscores

        if 'displaySpace' not in parsed_data or not parsed_data['displaySpace']:
            print(f"Warning: Could not parse 'displaySpace' from LUT filename '{lut_filename}' using pattern. Skipping.")
            return None

        # --- 6. Validate Shaper Space (if required by pattern) ---
        shaper_space_name = None
        if has_shaper_placeholder:
            if 'shaperSpace' not in parsed_data or not parsed_data['shaperSpace']:
                print(f"Warning: Pattern requires 'shaperSpace' but could not parse it from LUT filename '{lut_filename}'. Skipping.")
                return None

            extracted_shaper_identifier = parsed_data['shaperSpace']
            resolved_shaper_obj = self._get_colorspace_from_name(extracted_shaper_identifier)
            if resolved_shaper_obj:
                shaper_space_name = self.get_cs_name(resolved_shaper_obj)
            else:
                # Check if it's a role name that resolves
                role_resolved_name = self.roles.get(extracted_shaper_identifier)
                if role_resolved_name and self._get_colorspace_from_name(role_resolved_name):
                    shaper_space_name = role_resolved_name
                else:
                    # Prompt user for shaper space (if running interactively)
                    # In GUI mode, this function returning None signals the GUI to handle it.
                    # If running as a script, prompting might still be desired.
                    if sys.stdin.isatty(): # Check if running interactively
                        print(f"Info: Parsed shaper identifier '{extracted_shaper_identifier}' from LUT '{lut_filename}' does not match a known colorspace or role.")
                        shaper_space_name = self._prompt_for_colorspace(lut_filename, 'shaper')
                        if shaper_space_name is None:
                            return None # User skipped or input was invalid after prompts
                    else:
                        print(f"Warning: Parsed shaper identifier '{extracted_shaper_identifier}' from LUT '{lut_filename}' does not match a known colorspace or role. Cannot prompt in non-interactive mode. Skipping.")
                        return None


        # --- 7. Resolve and Validate Display Name to Full Colorspace Name ---
        display_identifier = parsed_data['displaySpace']
        resolved_display_obj = self._get_colorspace_from_name(display_identifier)
        if not resolved_display_obj:
            # Prompt user for display space (if running interactively)
            if sys.stdin.isatty():
                print(f"Info: Parsed display identifier '{display_identifier}' from LUT '{lut_filename}' does not match a known colorspace.")
                resolved_display_name = self._prompt_for_colorspace(lut_filename, 'display')
                if resolved_display_name is None:
                    return None # User skipped or input was invalid after prompts
                # If user provided input, we use that resolved name directly
                resolved_display_obj_name = resolved_display_name
            else:
                print(f"Warning: Parsed display identifier '{display_identifier}' from LUT '{lut_filename}' does not match a known colorspace. Cannot prompt in non-interactive mode. Skipping.")
                return None
        else:
            # If automatically resolved, use the object's full name
            resolved_display_obj_name = resolved_display_obj.name

        # Always use the full name for the display part of the view transform internally
        parsed_data['displaySpace'] = resolved_display_obj_name

        # --- 8. Return Parsed Info ---
        parsed_data['shaperSpace'] = shaper_space_name # Add resolved/None shaper name
        parsed_data['lutFilename'] = lut_filename # Add original filename (with extension)

        return parsed_data


    def create_config(self, view_transform_data=None, explicit_mutations=None):

        # Initialize basic config settings
        self.config.setMajorVersion(self.ocio_version_major)
        self.config.setMinorVersion(0) # Only support 1.0 or 2.0 for now
        # Set config name from settings
        config_name = self.settings.get("config_name", "generated_ocio_config")
        if config_name and self.ocio_version_major > 1:
            self.config.setName(config_name)
        # Set config description from settings
        config_description = self.settings.get("config_description", "")
        if config_description:
            # OCIO v1 does not support name property so we prefix it in the config description.
            if self.ocio_version_major < 2:
                config_description = f"{config_name}: {config_description}"
            self.config.setDescription(config_description)
        self.config.setSearchPath('luts:transfer_functions')

        # Create config directory inside the specified output directory
        self.config_dir = os.path.join(self.output_dir, config_name)
        try:
            if os.path.exists(self.config_dir):
                shutil.rmtree(self.config_dir)
            os.makedirs(self.config_dir)
            # Create luts/transfer_functions subdir immediately
            os.makedirs(os.path.join(self.config_dir, 'transfer_functions'), exist_ok=True)
            os.makedirs(os.path.join(self.config_dir, 'luts'), exist_ok=True)
        except OSError as e:
            print(f"Error creating config directory '{self.config_dir}': {e}")
            sys.exit(1)
        config_filename = f"{config_name}_ocio-v{self.ocio_version_major}.0.ocio"
        self.config_path = os.path.join(self.config_dir, config_filename)

        # Set roles from YAML data (excluding 'reference')
        for role_name, cs_identifier in self.roles.items():
            if role_name == ocio.ROLE_REFERENCE: # Use OCIO constant for clarity
                continue # Skip reference role if it somehow exists in YAML
            colorspace_obj = self._get_colorspace_from_name(cs_identifier)
            if colorspace_obj:
                # Use get_cs_name to respect the use_shortnames setting
                actual_cs_name = self.get_cs_name(colorspace_obj)
                if actual_cs_name:
                    self.config.setRole(role_name, actual_cs_name)
                else:
                    # This case should ideally not happen if colorspace_obj is valid
                    print(f"Warning: Could not determine name for colorspace '{cs_identifier}' for role '{role_name}'. Skipping.")
            else:
                print(f"Warning: Colorspace '{cs_identifier}' defined for role '{role_name}' not found or inactive. Skipping role.")

        # Explicitly set the 'reference' role based on the reference_colorspace setting
        actual_ref_cs_name = self.get_cs_name(self.reference_colorspace)
        if actual_ref_cs_name:
            print(f"Setting reference role to: {actual_ref_cs_name}")
            self.config.setRole(ocio.ROLE_REFERENCE, actual_ref_cs_name)
        else:
            print(f"Error: Could not determine name for reference colorspace '{self.settings.get('reference_colorspace')}'. Reference role not set.")


        # Add base colorspaces (from colorspaces.yaml) to the config
        print("Adding base colorspaces...")
        for c in self.colorspaces:
            cs = self.create_colorspace(c)
            if cs:
                try:
                    self.config.addColorSpace(cs)
                except ocio.Exception as e:
                    print(f"Error adding base colorspace '{self.get_cs_name(c)}' to config: {e}")

        # --- Process View Transforms ---
        # Use provided data if available, otherwise perform discovery
        if view_transform_data is not None:
            print("Using pre-processed view transform data...")
            discovered_luts_info = view_transform_data # Use the list passed from GUI
        else:
            print("Discovering LUTs and generating View Transforms...")
            view_transform_settings = self.settings.get('view_transform_settings', {})
            lut_search_path_setting = view_transform_settings.get('lut_search_path', '.') # Default to CWD if not specified
            # Default shaper role used ONLY if {shaperSpace} is NOT in the filename pattern
            default_shaper_role_if_unspecified = self.roles.get('color_timing', 'color_timing')

            # Resolve LUT search path: absolute or relative to CWD
            if os.path.isabs(lut_search_path_setting):
                full_search_dir = lut_search_path_setting
            else:
                full_search_dir = os.path.abspath(os.path.join(os.getcwd(), lut_search_path_setting))
            discovered_luts_info = [] # Store successfully parsed info: {'viewName':.., 'displaySpace':.., 'shaperSpace':.., 'lutFilename':.., 'originalPath':..}

            if not os.path.isdir(full_search_dir):
                print(f"Warning: LUT search directory '{full_search_dir}' not found. Skipping LUT discovery.")
            else:
                print(f"Searching for LUTs in: {full_search_dir}")
                # Find all files first, then attempt to parse
                for filename in os.listdir(full_search_dir):
                    filepath = os.path.join(full_search_dir, filename)
                    if os.path.isfile(filepath):
                        # Use internal parsing which includes prompting if needed (in interactive mode)
                        parsed_info = self._parse_lut_filename(filename) # This now checks extension and matches name part

                        if parsed_info: # Only proceed if parsing was successful
                            # Add the original path for copying later
                            parsed_info['originalPath'] = filepath
                            # Resolve default shaper only if shaper wasn't in pattern AND wasn't resolved
                            # Note: _parse_lut_filename now handles prompting if shaper is required but invalid
                            if parsed_info['shaperSpace'] is None and '{shaperSpace}' not in view_transform_settings.get('lut_filename_pattern', ''):
                                # Resolve role name to actual colorspace name if possible
                                shaper_cs_obj = self._get_colorspace_from_name(default_shaper_role_if_unspecified)
                                if shaper_cs_obj:
                                    parsed_info['shaperSpace'] = self.get_cs_name(shaper_cs_obj)
                                    print(f"Info: Using default shaper '{parsed_info['shaperSpace']}' (from role '{default_shaper_role_if_unspecified}') for LUT '{filename}'.")
                                else:
                                    print(f"Warning: Default shaper role '{default_shaper_role_if_unspecified}' does not resolve to a valid colorspace. Cannot set default shaper for '{filename}'.")
                                    # Decide if this is an error or just skip shaper
                                    # continue # Option: Skip LUT if default shaper is invalid

                            discovered_luts_info.append(parsed_info)
                        # else:
                            # If parsed_info is None, it means either invalid extension,
                            # pattern mismatch, or user skipped during prompt.
                            # In script mode, we just skip these files. The GUI will handle adding them.
                            # print(f"Debug: Skipping file '{filename}' (invalid extension or pattern mismatch/prompt skip).")

        # --- Generate Colorspaces and Prepare Display Structure ---
        generated_cs_objects = {} # Store generated OCIO ColorSpace objects keyed by name
        # Use OrderedDict to store {displaySpace: [(viewName, generatedCsName), ...]} to preserve order
        display_lut_view_mappings = OrderedDict() # Stores {display_fullname: [(viewName, csName), ...]}
        existing_display_view_pairs = set() # Stores (display_fullname, viewName) tuples for existing LUTs/mutations
        discovered_display_names = set()
        ref_cs_name = self.get_cs_name(self.reference_colorspace)

        # Get the family name for 'image' category
        category_map = {}
        for item in self.settings.get('category_folder_names', []):
            if isinstance(item, dict): category_map.update(item)
        image_family_name = category_map.get('image', 'Image Formation')

        if not ref_cs_name:
            print("Error: Cannot determine reference colorspace name. Aborting view transform generation.")
        else:
            print(f"Processing {len(discovered_luts_info)} view transforms...")
            for lut_info in discovered_luts_info:
                view_name = lut_info['viewName']
                display_name = lut_info['displaySpace'] # Already resolved to full name by parser
                shaper_space_name = lut_info['shaperSpace'] # Already validated or defaulted by parser
                lut_filename = lut_info['lutFilename']
                original_lut_path = lut_info['originalPath']

                # Add display name to set for later processing
                discovered_display_names.add(display_name) # display_name here is the full name from parser

                # Construct the name for the generated colorspace, using shortname for display if enabled
                display_cs_obj = self._get_colorspace_from_name(display_name)
                display_name_for_cs = self.get_cs_name(display_cs_obj) if display_cs_obj else display_name # Fallback if lookup fails
                generated_cs_name = f"{view_name} - {display_name_for_cs}"

                # Skip if already generated (e.g., duplicate LUT files somehow)
                if generated_cs_name in generated_cs_objects:
                    continue

                # --- Create the OCIO Colorspace Object ---
                vt_cs = ocio.ColorSpace()
                vt_cs.setName(generated_cs_name)
                vt_cs.setFamily(image_family_name)
                if self.settings.get('enable_descriptions', False):
                    # Use full display name in description for clarity, even if shortname is used in CS name
                    full_display_name = self._get_colorspace_from_name(display_name).name if self._get_colorspace_from_name(display_name) else display_name
                    vt_cs.setDescription(f"{view_name} view transform for {full_display_name} display (using {lut_filename}).")
                vt_cs.setBitDepth(ocio.BIT_DEPTH_F32)

                # Set encoding for view transform colorspace (OCIO v2+ and enabled)
                if self.ocio_version_major >= 2 and self.settings.get('enable_colorspace_encoding'):
                    # Determine encoding based on display name (using full name for check)
                    full_display_name_check = self._get_colorspace_from_name(display_name).name if self._get_colorspace_from_name(display_name) else display_name
                    if "Rec.2100" in full_display_name_check or "Dolby" in full_display_name_check:
                        vt_cs.setEncoding('hdr-video')
                    else:
                        vt_cs.setEncoding('sdr-video')

                # --- Create the Transform ---
                xforms = []
                # 1. Convert Reference -> Shaper Space
                shaper_cs_obj = self._get_colorspace_from_name(shaper_space_name)
                if not shaper_cs_obj:
                    # Check if it's a valid role name that resolves
                    role_resolved_name = self.roles.get(shaper_space_name)
                    if role_resolved_name:
                        shaper_cs_obj = self._get_colorspace_from_name(role_resolved_name)

                if not shaper_cs_obj:
                    print(f"Error: Shaper colorspace or role '{shaper_space_name}' (for LUT '{lut_filename}') not found or invalid. Skipping transform for '{generated_cs_name}'.")
                    continue # Skip this LUT/colorspace
                actual_shaper_name = self.get_cs_name(shaper_cs_obj) # Get name respecting shortnames
                if ref_cs_name != actual_shaper_name: # Still avoid adding identity transform
                    xforms.append(ocio.ColorSpaceTransform(src=ocio.ROLE_REFERENCE, dst=actual_shaper_name))

                # 2. Apply 3D LUT (FileTransform) - Copy LUT first
                dest_lut_dir = os.path.join(self.config_dir, 'luts')
                dest_lut_path = os.path.join(dest_lut_dir, lut_filename)
                try:
                    # print(f"Debug: Copying LUT from '{original_lut_path}' to '{dest_lut_path}'")
                    shutil.copy2(original_lut_path, dest_lut_path) # copy2 preserves metadata
                except Exception as e:
                    print(f"Error copying LUT '{lut_filename}' from '{original_lut_path}' to '{dest_lut_path}': {e}. Skipping transform.")
                    continue # Skip this LUT/colorspace

                # Path for OCIO FileTransform is relative to search path ('luts/')
                lut_path_for_ocio = lut_filename
                xforms.append(ocio.FileTransform(src=lut_path_for_ocio, interpolation=ocio.INTERP_TETRAHEDRAL))

                # Combine transforms
                if not xforms:
                    print(f"Warning: No transforms generated for view transform '{generated_cs_name}'.")
                    continue
                elif len(xforms) == 1:
                    vt_cs.setTransform(xforms[0], ocio.COLORSPACE_DIR_FROM_REFERENCE)
                else:
                    grp_xform = ocio.GroupTransform()
                    for xform in xforms: grp_xform.appendTransform(xform)
                    vt_cs.setTransform(grp_xform, ocio.COLORSPACE_DIR_FROM_REFERENCE)

                # Store generated object and mapping (using the list structure)
                generated_cs_objects[generated_cs_name] = vt_cs
                if display_name not in display_lut_view_mappings:
                    display_lut_view_mappings[display_name] = []
                # Append tuple to preserve order for later sorting
                display_lut_view_mappings[display_name].append((view_name, generated_cs_name))
                existing_display_view_pairs.add((display_name, view_name)) # Track existing pair

        # --- Add Generated Colorspaces to Config ---
        print(f"Adding {len(generated_cs_objects)} generated View Transform colorspaces...")
        for cs_name, cs_obj in generated_cs_objects.items():
            try:
                # Check if colorspace already exists before adding
                # This check might be redundant if generated_cs_objects keys are unique, but safe to keep.
                if not self.config.getColorSpace(cs_name):
                    self.config.addColorSpace(cs_obj)
                # else:
                #     print(f"Debug: Colorspace '{cs_name}' already added (likely from base colorspaces).")
            except ocio.Exception as e:
                print(f"Error adding generated colorspace '{cs_name}' to config: {e}")

        # --- Apply View Mutations (either from rules or explicit list) ---
        if explicit_mutations is not None:
            # Process mutations explicitly passed from GUI
            print(f"Processing {len(explicit_mutations)} explicit view mutations from GUI...") # Now expects (source_view_cs_name, source_display_name_for_transform, target_display_fullname, view_name)
            for source_view_cs_name, source_display_name_for_transform, target_display_fullname, view_name in explicit_mutations:
                # Basic validation
                source_view_cs_obj = generated_cs_objects.get(source_view_cs_name) # Source *view* CS must exist from LUT processing
                target_display_obj = self._get_colorspace_from_name(target_display_fullname) # Target *display* CS must exist

                if not source_view_cs_obj:
                    print(f"  Warning: Source view colorspace '{source_view_cs_name}' for explicit mutation not found in generated objects. Skipping.")
                    continue
                if not target_display_obj:
                    print(f"  Warning: Target display colorspace '{target_display_fullname}' for explicit mutation not found or inactive. Skipping.")
                    continue

                target_display_name_for_cs = self.get_cs_name(target_display_obj) # Name respecting shortnames for new CS name
                mutated_cs_name = f"{view_name} - {target_display_name_for_cs}"

                if mutated_cs_name in generated_cs_objects:
                    print(f"  Info: Explicitly requested mutated colorspace '{mutated_cs_name}' already generated. Skipping duplicate.")
                    continue

                print(f"  Generating explicitly requested mutation: '{mutated_cs_name}'")
                mutated_cs_obj = ocio.ColorSpace()
                mutated_cs_obj.setName(mutated_cs_name)
                mutated_cs_obj.setFamily(source_view_cs_obj.getFamily()) # Use source *view* CS for family/bitdepth/encoding
                mutated_cs_obj.setBitDepth(source_view_cs_obj.getBitDepth())
                if self.settings.get('enable_descriptions', False):
                     mutated_cs_obj.setDescription(f"{view_name} view transform for {target_display_fullname} display (mutated from {source_view_cs_name}).")
                if self.ocio_version_major >= 2 and self.settings.get('enable_colorspace_encoding'):
                     mutated_cs_obj.setEncoding(source_view_cs_obj.getEncoding())

                # Transform Construction
                transform_to_source_view = ocio.ColorSpaceTransform(src=ocio.ROLE_REFERENCE, dst=source_view_cs_name)
                source_display_cs_name = source_display_name_for_transform # Use the name passed from GUI
                target_display_cs_name = self.get_cs_name(target_display_obj)
                display_conversion_transform = ocio.ColorSpaceTransform(src=source_display_cs_name, dst=target_display_cs_name)

                combined_transform = ocio.GroupTransform()
                combined_transform.appendTransform(transform_to_source_view)
                combined_transform.appendTransform(display_conversion_transform)
                mutated_cs_obj.setTransform(combined_transform, ocio.COLORSPACE_DIR_FROM_REFERENCE)

                # Add to config and tracking
                try:
                    if not self.config.getColorSpace(mutated_cs_name):
                        self.config.addColorSpace(mutated_cs_obj)
                        generated_cs_objects[mutated_cs_name] = mutated_cs_obj
                        # Add to display_lut_view_mappings for final structure generation
                        if target_display_fullname not in display_lut_view_mappings:
                            display_lut_view_mappings[target_display_fullname] = []
                        # Ensure we don't add duplicate view tuples if somehow processed twice
                        if (view_name, mutated_cs_name) not in display_lut_view_mappings[target_display_fullname]:
                             display_lut_view_mappings[target_display_fullname].append((view_name, mutated_cs_name))
                        # No need to update existing_display_view_pairs here, as GUI handled existence check
                    # else: # Already exists, skip adding
                except ocio.Exception as e:
                    print(f"    Error adding explicitly mutated colorspace '{mutated_cs_name}' to config: {e}")

        elif self.view_mutate_rules:
            # --- Apply View Mutate Rules (Original logic if not called from GUI with explicit list) ---
            print("Applying view_mutate rules from settings...")
            # (Keep the original mutation logic here, indented under this 'elif')
            for source_display_shortname, target_display_shortnames in self.view_mutate_rules.items():
                source_display_obj = self._get_colorspace_from_name(source_display_shortname)
                if not source_display_obj:
                    print(f"  Warning: Source display '{source_display_shortname}' in view_mutate rule not found or inactive. Skipping rule.")
                    continue
                source_display_fullname = source_display_obj.name # Use full name for internal mapping key

                if source_display_fullname not in display_lut_view_mappings:
                    continue # No views to mutate from

                print(f"  Processing mutations from source: {source_display_fullname}")
                for view_name, source_cs_name in list(display_lut_view_mappings[source_display_fullname]):
                    source_cs_obj = generated_cs_objects.get(source_cs_name)
                    if not source_cs_obj:
                        print(f"    Warning: Could not find source colorspace object '{source_cs_name}' for view '{view_name}'. Skipping mutation.")
                        continue

                    # Ensure target_display_shortnames is iterable before looping
                    if not target_display_shortnames:
                        print(f"    Info: No target displays defined for source '{source_display_fullname}' in view_mutate rule. Skipping.")
                        continue # Skip to the next source view

                    for target_display_shortname in target_display_shortnames:
                        target_display_obj = self._get_colorspace_from_name(target_display_shortname)
                        if not target_display_obj:
                            print(f"    Warning: Target display '{target_display_shortname}' in view_mutate rule not found or inactive. Skipping target.")
                            continue
                        target_display_fullname = target_display_obj.name
                        target_display_name_for_cs = self.get_cs_name(target_display_obj)

                        if (target_display_fullname, view_name) in existing_display_view_pairs:
                            continue

                        print(f"    Mutating view '{view_name}' for target display '{target_display_fullname}'...")
                        mutated_cs_name = f"{view_name} - {target_display_name_for_cs}"

                        if mutated_cs_name in generated_cs_objects:
                            continue

                        mutated_cs_obj = ocio.ColorSpace()
                        mutated_cs_obj.setName(mutated_cs_name)
                        mutated_cs_obj.setFamily(source_cs_obj.getFamily())
                        mutated_cs_obj.setBitDepth(source_cs_obj.getBitDepth())
                        if self.settings.get('enable_descriptions', False):
                             mutated_cs_obj.setDescription(f"{view_name} view transform for {target_display_fullname} display (mutated from {source_display_fullname} LUT).")
                        if self.ocio_version_major >= 2 and self.settings.get('enable_colorspace_encoding'):
                             mutated_cs_obj.setEncoding(source_cs_obj.getEncoding())

                        transform_to_source_view = ocio.ColorSpaceTransform(src=ocio.ROLE_REFERENCE, dst=source_cs_name)
                        source_display_cs_name = self.get_cs_name(source_display_obj)
                        target_display_cs_name = self.get_cs_name(target_display_obj)

                        if not source_display_cs_name or not target_display_cs_name:
                             print(f"      Error: Could not resolve source display ('{source_display_cs_name}') or target display ('{target_display_cs_name}') name for transform. Skipping mutation.")
                             continue

                        display_conversion_transform = ocio.ColorSpaceTransform(src=source_display_cs_name, dst=target_display_cs_name)

                        combined_transform = ocio.GroupTransform()
                        combined_transform.appendTransform(transform_to_source_view)
                        combined_transform.appendTransform(display_conversion_transform)
                        mutated_cs_obj.setTransform(combined_transform, ocio.COLORSPACE_DIR_FROM_REFERENCE)

                        try:
                            if not self.config.getColorSpace(mutated_cs_name):
                                self.config.addColorSpace(mutated_cs_obj)
                                generated_cs_objects[mutated_cs_name] = mutated_cs_obj
                                if target_display_fullname not in display_lut_view_mappings:
                                    display_lut_view_mappings[target_display_fullname] = []
                                display_lut_view_mappings[target_display_fullname].append((view_name, mutated_cs_name))
                                existing_display_view_pairs.add((target_display_fullname, view_name))
                                print(f"      Successfully added mutated colorspace: {mutated_cs_name}")
                        except ocio.Exception as e:
                            print(f"      Error adding mutated colorspace '{mutated_cs_name}' to config: {e}")
        else:
             print("No view_mutate rules in settings and no explicit mutations provided.")

        # --- Build Final Display/View Structure (Ordered) ---
        final_display_structure = OrderedDict() # Use OrderedDict {display_fullname: [(viewName, csName), ...], ...}
        ordered_active_views_list = [] # Store the ordered view names for the *first* active display

        # Process displays based on the order they were encountered (preserved by OrderedDict)
        # This includes displays that only have mutated views now.
        all_processed_display_fullnames = list(display_lut_view_mappings.keys())

        for display_name in all_processed_display_fullnames:
            # Start with LUT-based and mutated views, preserving their order from display_lut_view_mappings
            views_for_this_display = display_lut_view_mappings.get(display_name, [])

            # Get base display and bypass colorspace objects/names
            display_cs = self._get_colorspace_from_name(display_name)
            bypass_cs = self._get_colorspace_from_name('bypass')

            # Prepare tuples for Display Encoding and Bypass views
            display_encoding_view_tuple = None
            if display_cs:
                display_encoding_view_tuple = ("Display Encoding", self.get_cs_name(display_cs))
            else:
                print(f"Warning: Base colorspace for display '{display_name}' not found. Cannot add 'Display Encoding' view.")

            bypass_view_tuple = None
            if bypass_cs:
                bypass_view_tuple = ("Bypass", self.get_cs_name(bypass_cs))
            else:
                print("Warning: Base colorspace 'bypass' not found. Cannot add 'Bypass' view.")

            # Append Display Encoding and Bypass views *after* other views
            if display_encoding_view_tuple:
                views_for_this_display.append(display_encoding_view_tuple)
            if bypass_view_tuple:
                views_for_this_display.append(bypass_view_tuple)

            # Store the final ordered list for this display
            if views_for_this_display:
                final_display_structure[display_name] = views_for_this_display

        # --- Default Fallback (if no displays discovered) ---
        if not final_display_structure:
            print("Info: No valid LUTs discovered. Adding default 'Rec.1886 Display'.")
            default_display_name = "Rec.1886 Display"
            default_ordered_views = []
            rec1886_cs = self._get_colorspace_from_name('rec1886')
            bypass_cs = self._get_colorspace_from_name('bypass')

            # Add Display Encoding (if possible)
            display_encoding_view_tuple = None
            if rec1886_cs:
                display_encoding_view_tuple = ("Display Encoding", self.get_cs_name(rec1886_cs))
                default_ordered_views.append(display_encoding_view_tuple)
            else:
                print("Error: Default fallback failed. Base colorspace 'rec1886' not found.")

            # Add Bypass (if possible)
            bypass_view_tuple = None
            if bypass_cs:
                bypass_view_tuple = ("Bypass", self.get_cs_name(bypass_cs))
                default_ordered_views.append(bypass_view_tuple)
            else:
                print("Error: Default fallback failed. Base colorspace 'bypass' not found.")

            if default_ordered_views: # Only add if essential views could be mapped
                final_display_structure[default_display_name] = default_ordered_views

        # --- Set Displays/Views in OCIO Config (Ordered) ---
        print("Setting up Displays and Views in OCIO config...")
        if final_display_structure:
            # Get active displays in the order they were processed (preserved by OrderedDict)
            active_displays_list = list(final_display_structure.keys())
            active_displays_str = ', '.join(active_displays_list)
            self.config.setActiveDisplays(active_displays_str)

            # Collect all unique view names from all active displays
            all_view_names = set()
            for display_name in active_displays_list:
                views_for_display = final_display_structure.get(display_name, [])
                for view_name, _ in views_for_display:
                    all_view_names.add(view_name)

            # Determine the order of active views based on the first active display
            # This maintains a consistent order for setActiveViews across all displays
            ordered_active_views_list = []
            if active_displays_list:
                first_display_name = active_displays_list[0]
                views_for_first_display = final_display_structure.get(first_display_name, [])
                ordered_active_views_list = [view_name for view_name, _ in views_for_first_display]
            else:
                # Fallback if no active displays (shouldn't happen if fallback logic works)
                all_view_names = set()
                for display_name in active_displays_list: # Iterate over potentially empty list
                    views_for_display = final_display_structure.get(display_name, [])
                    for view_name, _ in views_for_display:
                        all_view_names.add(view_name)
                # Simple alphabetical sort as a last resort if first display had no views
                ordered_active_views_list = sorted(list(all_view_names))

            active_views_str = ', '.join(ordered_active_views_list)
            self.config.setActiveViews(active_views_str)

            print(f"Set active displays: {active_displays_str}")
            print(f"Set active views: {active_views_str}")

            # Add views in the determined order
            for display_name, ordered_views in final_display_structure.items():
                print(f"  Adding views for display: {display_name}")
                for view_name, cs_name in ordered_views:
                    try:
                        # Check target CS exists
                        if self.config.getColorSpace(cs_name):
                            print(f"    - {view_name} -> {cs_name}")
                            self.config.addDisplayView(display=display_name, view=view_name, colorSpaceName=cs_name)
                        else:
                            print(f"    - Error: Target colorspace '{cs_name}' for view '{view_name}' not found. Skipping.")
                    except ocio.Exception as e:
                        print(f"    - Error adding view '{view_name}': {e}")
        else:
            print("Warning: No displays or views configured (discovery and fallback failed).")


        # Validate and save the ocio config
        print(f'\nValidating final config... ')
        try:
            self.config.validate()
            print("Validation successful.")
            cfg = self.config.serialize()
            cfg = self._unbloat(cfg)
            with open(self.config_path, 'w') as f:
                f.write(cfg)
            print(f"Config generated successfully at: {self.config_path}\n")
        except ocio.Exception as e:
            print(f"OCIO Validation Error: {e}")
            print("Config generation failed.")


    def get_cs_name(self, c):
        # Get correct colorspace name depending on whether use_shortnames is enabled
        if not c: return None
        if self.settings.get('use_shortnames') and c.shortname:
            return c.shortname
        else:
            return c.name


    def create_colorspace(self, c):
        """Create an OCIO colorspace from a Colorspace dataclass object"""
        # Set up basic parameters of the OCIO Colorspace object
        cs = ocio.ColorSpace()
        cs_name_actual = self.get_cs_name(c) # Get the name respecting shortname setting
        if not cs_name_actual:
            # This should ideally be caught earlier in _get_colorspaces
            print(f"Error: Cannot create colorspace, name could not be determined for: {c}")
            return None

        try:
            cs.setName(cs_name_actual)

            if self.ocio_version_major >= 2 and c.alias and self.settings.get('enable_colorspace_aliases'):
                cs.addAlias(c.alias)
            if c.description and self.settings.get('enable_descriptions', False):
                if self.settings.get('verbose_descriptions', False):
                    cs.setDescription(c.description)
                else:
                    cs.setDescription(c.name) # Use original name for non-verbose description

            # Set Family based on colorspace category, if there is a mapping defined
            if c.category:
                # Correctly handle list of dicts for category mapping
                category_map = {}
                for item in self.settings.get('category_folder_names', []):
                    if isinstance(item, dict):
                        category_map.update(item)
                family = category_map.get(c.category)
                if family:
                    cs.setFamily(family)
            cs.setBitDepth(ocio.BIT_DEPTH_F32)

            direction = ocio.COLORSPACE_DIR_TO_REFERENCE if c.forward else ocio.COLORSPACE_DIR_FROM_REFERENCE

            # list of transforms to be applied
            xforms = []

            # Transfer Functions
            if c.tf:
                if callable(c.tf):
                    # Create spi1d from python function
                    lut_filename = f'{c.tf.__name__}_to_linear.spi1d'
                    # Ensure lut_dir uses self.config_dir which is guaranteed to exist
                    lut_dir = os.path.join(self.config_dir, 'transfer_functions')

                    if 'oetf' in c.tf.__name__:
                        lut_filename = self._generate_spi1d(c.tf, lut_filename, lut_dir, mn=-0.15, mx=1.2, inv=True, LUT_SIZE=self.LUT_SIZE)
                        if lut_filename: # Check if LUT generation succeeded
                            xforms.append(ocio.FileTransform(lut_filename))

                    elif 'eotf' in c.tf.__name__ or 'eocf' in c.tf.__name__:
                        lut_filename = self._generate_spi1d(c.tf, lut_filename, lut_dir, mn=0.0, mx=1.2, inv=False, LUT_SIZE=self.LUT_SIZE)
                        if lut_filename: # Check if LUT generation succeeded
                            xforms.append(ocio.FileTransform(src=lut_filename, direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE))
                    else:
                        # Handle cases where function name doesn't indicate direction clearly
                        # Defaulting to forward (TO_REFERENCE) lut generation if direction unclear
                        print(f"Warning: Direction (OETF/EOTF) unclear for TF '{c.tf.__name__}' in '{cs_name_actual}'. Assuming forward LUT generation.")
                        lut_filename = self._generate_spi1d(c.tf, lut_filename, lut_dir, mn=0.0, mx=1.0, inv=False, LUT_SIZE=self.LUT_SIZE) # Example default range
                        if lut_filename: # Check if LUT generation succeeded
                            xforms.append(ocio.FileTransform(lut_filename))


                elif isinstance(c.tf, ocio.Transform):
                    xforms.append(c.tf) # Already an OCIO transform (e.g., from builtin)

            # Gamut Conversions
            if isinstance(c.chr, list):
                # Convert RGBW xy Chromaticities into 3x3 matrix which converts to Reference Gamut
                if self.reference_colorspace and isinstance(self.reference_colorspace.chr, list):
                    try:
                        mtx = rgb_to_rgb(c.chr, self.reference_colorspace.chr)
                        if not is_identity(mtx):
                            xforms.append(ocio.MatrixTransform(pad_4x4(mtx)))
                    except Exception as e:
                        print(f"Error calculating gamut matrix for '{cs_name_actual}': {e}")
                else:
                    print(f"Warning: Cannot perform matrix gamut conversion for '{cs_name_actual}'. Reference colorspace or its chromaticities missing/invalid.")
            elif isinstance(c.chr, str):
                # Gamut conversion is a reference to another colorspace (by name/shortname)
                # This referenced colorspace defines the primaries for the current colorspace 'c'.
                # The transform should convert between this referenced gamut and the reference role.
                referenced_cs_obj = self._get_colorspace_from_name(c.chr)
                if referenced_cs_obj:
                        referenced_cs_name_actual = self.get_cs_name(referenced_cs_obj)
                        if referenced_cs_name_actual:
                                # The direction depends on whether the *current* colorspace 'c' is defined
                                # as TO_REFERENCE (forward=True) or FROM_REFERENCE (forward=False).
                                # If c.forward is True, we need a transform FROM the referenced gamut TO the reference role.
                                # If c.forward is False, we need a transform FROM the reference role TO the referenced gamut.
                                if c.forward:
                                        # Transform from referenced gamut TO reference role
                                        xforms.append(ocio.ColorSpaceTransform(src=referenced_cs_name_actual, dst=ocio.ROLE_REFERENCE))
                                else:
                                        # Transform from reference role TO referenced gamut
                                        xforms.append(ocio.ColorSpaceTransform(src=ocio.ROLE_REFERENCE, dst=referenced_cs_name_actual))
                        elif not referenced_cs_name_actual:
                                    print(f"Warning: Could not determine name for referenced colorspace '{c.chr}' in '{cs_name_actual}'. Skipping gamut transform.")
                        # else: referenced space *is* the reference space, no transform needed.
            # No 'else' needed - if c.chr is None or invalid type, no gamut transform is added.

            # Apply transforms to the colorspace object
            if not xforms:
                # Check if it's the reference space itself or data space
                is_ref = self.reference_colorspace and cs_name_actual == self.get_cs_name(self.reference_colorspace)
                is_data = c.encoding == 'data'
                if not is_ref and not is_data:
                    print(f"Warning: Colorspace '{cs_name_actual}' has no transforms defined and is not the reference or data space.")
            elif len(xforms) == 1:
                cs.setTransform(xforms[0], direction=direction)
            else: # len(xforms) > 1
                if not c.forward:
                    xforms = xforms[::-1]  # Reverse order for FROM_REFERENCE
                grp_xform = ocio.GroupTransform()
                for xform in xforms:
                    grp_xform.appendTransform(xform)
                cs.setTransform(grp_xform, direction=direction)

            # Set Allocation and Encoding (OCIO v1/v2 specifics)
            if self.ocio_version_major < 2:
                # OCIO v1: Set lg2 allocation for linear spaces (no transfer function defined)
                if not c.tf:
                    cs.setAllocation(ocio.ALLOCATION_LG2)
                    cs.setAllocationVars(self.allocation_vars)
                else:
                    cs.setAllocation(ocio.ALLOCATION_UNIFORM) # Uniform allocation for nonlinear spaces.
            else:
                # OCIO v2: Set encoding based on YAML definition, only if enabled
                if self.settings.get('enable_colorspace_encoding'):
                    valid_encodings = ['scene-linear', 'log', 'sdr-video', 'hdr-video', 'data']
                    if c.encoding and c.encoding in valid_encodings:
                        cs.setEncoding(c.encoding)
                    elif c.encoding:
                        print(f"Warning: Invalid encoding '{c.encoding}' for colorspace '{cs_name_actual}'. Encoding not set.")

            return cs

        except ocio.Exception as e:
            print(f"Error during creation of colorspace '{cs_name_actual}': {e}")
            return None
        except Exception as e:
            print(f"Unexpected Python error during creation of colorspace '{cs_name_actual}': {e}")
            return None


    def _linspace(self, mn, mx, cnt):
        # return evenly spaced list of cnt numbers between mn and mx, including mx
        assert isinstance(cnt, int) and (cnt > 2)
        step = (mx - mn) / float(cnt-1)
        return itertools.islice(itertools.count(mn, step), cnt)

    def _generate_spi1d(self, fn, lut_filename, output_dir, inv=False, mn=0.0, mx=1.0, LUT_SIZE=2**13):
        """Generate a 1D LUT as an spi1d file (moved into class)"""
        lut_filepath = os.path.join(output_dir, lut_filename)
        try:
            # Generate evenly spaced values using the class method _linspace
            y = [str(round(fn(x, inv=inv), 9)) for x in self._linspace(mn, mx, LUT_SIZE)]

            # Write the spi1d file
            contents = f'Version 1\nFrom {mn} {mx}\nLength {LUT_SIZE}\nComponents 1\n{{\n'
            contents += '\n'.join(y)
            contents += '\n}'
            with open(lut_filepath, 'w') as f:
                f.write(contents)
            if not os.path.isfile(lut_filepath):
                # This shouldn't happen if write succeeded, but check anyway
                raise OSError(f"Failed to write LUT file: {lut_filepath}")
            # print(f"Generated LUT: {lut_filepath}") # Optional debug
            return lut_filename
        except Exception as e:
            print(f"Error generating LUT '{lut_filename}' for function '{fn.__name__}': {e}")
            # Returning None indicates failure to generate the LUT filename
            return None


    def _OCIO_LogCameraTransform(self, linSideBreak=None, logSideSlope=None, logSideOffset=None, linSideSlope=None, linSideOffset=None, linearSlope=None, base=None, direction='inverse', **kwargs):
        ''' Helper function to create an OCIO Camera Transform using keyword args'''
        params = {}
        if linSideBreak is not None: params['linSideBreak'] = [linSideBreak]*3
        if logSideSlope is not None: params['logSideSlope'] = [logSideSlope]*3
        if logSideOffset is not None: params['logSideOffset'] = [logSideOffset]*3
        if linSideSlope is not None: params['linSideSlope'] = [linSideSlope]*3
        if linSideOffset is not None: params['linSideOffset'] = [linSideOffset]*3
        if base is not None: params['base'] = base # Added base parameter
        params['direction'] = ocio.TransformDirection.TRANSFORM_DIR_INVERSE if direction == 'inverse' else ocio.TransformDirection.TRANSFORM_DIR_FORWARD

        xform = ocio.LogCameraTransform(**params)

        if linearSlope is not None:
            xform.setLinearSlopeValue([linearSlope]*3)

        return xform

    def _OCIO_LogAffineTransform(self, logSideSlope=None, logSideOffset=None, linSideSlope=None, linSideOffset=None, base=None, direction='inverse', **kwargs):
        ''' Helper function to create an OCIO LogAffine Transform using keyword args'''
        params = {}
        if logSideSlope is not None: params['logSideSlope'] = [logSideSlope]*3
        if logSideOffset is not None: params['logSideOffset'] = [logSideOffset]*3
        if linSideSlope is not None: params['linSideSlope'] = [linSideSlope]*3
        if linSideOffset is not None: params['linSideOffset'] = [linSideOffset]*3
        if base is not None: params['base'] = base
        params['direction'] = ocio.TransformDirection.TRANSFORM_DIR_INVERSE if direction == 'inverse' else ocio.TransformDirection.TRANSFORM_DIR_FORWARD

        return ocio.LogAffineTransform(**params)

    def _OCIO_ExponentWithLinearTransform(self, gamma=None, offset=None, negativeStyle=None, direction='inverse', **kwargs):
        '''OCIO ExponentWithLinear transform using keyword args'''
        ocio_direction = ocio.TransformDirection.TRANSFORM_DIR_INVERSE if direction.lower() == 'inverse' else ocio.TransformDirection.TRANSFORM_DIR_FORWARD

        xform = ocio.ExponentWithLinearTransform()
        xform.setDirection(ocio_direction)
        if gamma is not None: xform.setGamma([gamma]*4)
        if offset is not None: xform.setOffset([offset]*4)

        if negativeStyle is not None:
            style_map = {
                'pass_thru': ocio.NEGATIVE_PASS_THRU,
                'clamp': ocio.NEGATIVE_CLAMP,
                'mirror': ocio.NEGATIVE_MIRROR
            }
            ocio_style = style_map.get(negativeStyle.lower())
            if ocio_style is not None:
                xform.setNegativeStyle(ocio_style)
            else:
                print(f"Warning: Invalid negativeStyle '{negativeStyle}' for ExponentWithLinearTransform. Using default.")

        return xform

    def _OCIO_ExponentTransform(self, value=None, negativeStyle=None, direction='inverse', **kwargs):
        ''' OCIO ExponentTransform using keyword args'''
        ocio_direction = ocio.TransformDirection.TRANSFORM_DIR_INVERSE if direction.lower() == 'inverse' else ocio.TransformDirection.TRANSFORM_DIR_FORWARD

        params = {
            'value': [value]*4 if value is not None else [1.0]*4,
            'direction': ocio_direction
        }
        xform = ocio.ExponentTransform(**params)

        if negativeStyle is not None:
            style_map = {
                'pass_thru': ocio.NEGATIVE_PASS_THRU,
                'clamp': ocio.NEGATIVE_CLAMP,
                'mirror': ocio.NEGATIVE_MIRROR
            }
            ocio_style = style_map.get(negativeStyle.lower())
            if ocio_style is not None:
                xform.setNegativeStyle(ocio_style)
            else:
                print(f"Warning: Invalid negativeStyle '{negativeStyle}' for ExponentTransform. Using default.")

        return xform

    # def _OCIO_BuiltinTransform(self, style=None, direction='inverse', **kwargs):
    def _OCIO_BuiltinTransform(self, style=None, direction='inverse', **kwargs):
        ''' OCIO BuiltinTransform using keyword args'''
        ocio_direction = ocio.TransformDirection.TRANSFORM_DIR_INVERSE if direction.lower() == 'inverse' else ocio.TransformDirection.TRANSFORM_DIR_FORWARD
        if style:
            # Check if the style string is a valid OCIO BuiltinStyle attribute
            if hasattr(ocio, style):
                # OCIO Python bindings might expect the style name directly as a string
                # or potentially the attribute itself. Let's try the string first.
                try:
                    return ocio.BuiltinTransform(style=style, direction=ocio_direction)
                except ocio.Exception as e:
                    print(f"Error creating BuiltinTransform with style '{style}': {e}")
                    return None
                except TypeError as e:
                    # Handle potential API changes or unexpected errors
                    print(f"TypeError creating BuiltinTransform with style '{style}': {e}")
                    return None
            else:
                print(f"Warning: Invalid BuiltinTransform style '{style}'. Style must be a valid OCIO BuiltinStyle attribute name (e.g., 'UTILITY_CURVE_SRGB').")
                return None
        else:
            print("Warning: BuiltinTransform requires a 'style' parameter.")
            return None


    def _unbloat(self, cfg):
        '''Strip useless colorspace defaults bloating the config'''
        indent = '    '
        cfg = cfg.replace(f'{indent}equalitygroup: ""\n', '') # unspecified equalitygroup is unecessary
        cfg = cfg.replace(f'{indent}isdata: false\n', '') # isdata: false is the default.
        cfg = cfg.replace(f'{indent}allocation: uniform\n', '') # uniform 0-1 allocation is default.
        cfg = cfg.replace(f'{indent}allocationvars: [0, 1]\n', '') # uniform 0-1 allocation is default.
        cfg = cfg.replace(f'{indent}bitdepth: 32f\n', '') # bitdepth 32f is the default

        # Always replace scene_reference terminology
        cfg = cfg.replace('to_scene_reference: ', 'to_reference: ')
        cfg = cfg.replace('from_scene_reference: ', 'from_reference: ')

        # Basic cleanup of potentially multiple blank lines, but less aggressive
        # cfg = re.sub(r'\n\s*\n', '\n', cfg) # Keep this commented for now
        return cfg.strip() # Remove leading/trailing whitespace


__all__ = [
    "Colorspace",
    "OCIOConfig",
    "VALID_LUT_EXTENSIONS"
]