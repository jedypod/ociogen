# OCIOGen Documentation

## Table of Contents

- [OCIOGen Documentation](#ociogen-documentation)
  - [Table of Contents](#table-of-contents)
  - [Project Overview](#project-overview)
  - [Installation](#installation)
  - [Running the Software](#running-the-software)
  - [Graphical User Interface Usage (`ociogengui.py`)](#graphical-user-interface-usage-ociogenguipy)
    - [General Settings Tab](#general-settings-tab)
    - [Colorspaces \& Roles Tab](#colorspaces--roles-tab)
    - [View Transforms Tab](#view-transforms-tab)
    - [Bottom Controls](#bottom-controls)
  - [Configuration Files (YAML)](#configuration-files-yaml)
    - [`config_settings.yaml`](#config_settingsyaml)
      - [`settings`](#settings)
      - [`roles`](#roles)
      - [`active_colorspaces`](#active_colorspaces)
      - [`colorspaces`](#colorspaces)
    - [`colorspaces.yaml`](#colorspacesyaml)
  - [Command-Line Usage (`ociogen.py`)](#command-line-usage-ociogenpy)

---

## Project Overview

**OCIOGen** is a tool designed to simplify the creation and management of OpenColorIO (OCIO) configuration files. It provides both a command-line interface (`ociogen.py`) and a graphical user interface (`ociogengui.py`) to generate OCIO configs based on user-defined colorspace definitions and LUTs. All colorimetry math is built in, so all you need to provide for each colorspace is a set of CIE xy chromaticities, a transfer function and your desired reference space. The gamut conversion matrices to or from your reference space are calculated automatically.

**Key Features:**

*   **GUI for Interactive Configuration:** An intuitive interface to manage settings, select active colorspaces, configure roles, discover/edit/mutate view transforms, and generate the final config.
*   **Flexible Colorspace Definitions:** Easily define custom colorspaces from CIE xy chromaticities, custom transfer functions based on a python function or OCIO v2 Built-in transform, with additional attributes like category, encodings, and aliases.
*   **OCIO v1/v2 Compatibility:** Generate configs targeting either major OCIO version.
*   **YAML-based Configuration:** Define core settings, roles, active colorspaces, and colorspace definitions in human-readable YAML files.
*   **Automatic LUT Discovery:** Find user-provided LUTs and parse view name, shaper space and display space based on configurable filename patterns.
*   **View Transform Generation:** Automatically create the necessary OCIO colorspaces and transforms for discovered LUTs.
*   **View Mutation:** Automatically generate additional view transforms for different displays based on existing LUTs and mutation rules. For example, to automatically create "sRGB Display" views from a Rec.1886 LUT.
*   **Built-in Transform Support (OCIOv2):** Optionally use OCIOv2 built-in mathematical transforms instead of generating 1D LUTs for transfer functions (use with caution due to precision issues).


---

## Installation

This project requires Python 3.7+ and the following Python libraries:

*   **PyOpenColorIO:** For interacting with the OCIO library.
*   **PyYAML:** For reading the YAML configuration files.

You can install these dependencies using `pip` (Python's standard package installer) or Astral's `uv`.

**Option 1: Using `pip` and `venv` (Standard)**

1.  **Create a Virtual Environment (Optional but Recommended):**
    ```bash
    python -m venv venv
    ```

2.  **Activate the Virtual Environment:**
    *   **Linux/macOS:**
        ```bash
        source venv/bin/activate
        ```
    *   **Windows (Command Prompt):**
        ```bash
        venv\Scripts\activate.bat
        ```
    *   **Windows (PowerShell):**
        ```bash
        venv\Scripts\Activate.ps1
        ```

3.  **Install Dependencies:**
    ```bash
    python3 -m pip install PyOpenColorIO PyYAML
    ```
    *(Note: Ensure `pip` corresponds to your Python 3 installation. You might need to use `pip3` on some systems.)*

**Option 2: Using `uv` (Fast Alternative)**

[uv](https://github.com/astral-sh/uv) is a very fast Python package installer and resolver.

1.  **Install `uv`:** Follow the instructions on the [uv website](https://astral.sh/uv#installation).

2.  **Create Virtual Environment and Install Dependencies:**
    `uv` can create the environment and install packages in one step. Run this in the project's root directory:
    ```bash
    uv venv
    uv pip install PyOpenColorIO PyYAML
    ```
    This creates a `.venv` directory and installs the packages into it.

3.  **Activate the Environment (Optional for `uv run`):**
    You can activate the environment created by `uv` like a standard `venv`:
    *   **Linux/macOS:** `source .venv/bin/activate`
    *   **Windows (Cmd):** `.venv\Scripts\activate.bat`
    *   **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`

    Alternatively, you can use `uv run` to execute commands within the environment without activating it explicitly (see [Running the Software](#running-the-software)).

---

## Running the Software

Once dependencies are installed (using either `pip` or `uv`):

*   **If you activated the virtual environment:**
    ```bash
    # Run the GUI
    python ociogengui.py

    # Run the command-line tool
    python ociogen.py
    ```

*   **If using `uv` without activating the environment:**
    ```bash
    # Run the GUI
    uv run python ociogengui.py

    # Run the command-line tool
    uv run python ociogen.py
    ```

---

## Graphical User Interface Usage (`ociogengui.py`)

The GUI provides an interactive way to configure and generate the OCIO config. It is built with tkinter, so it should work out of the box with python on your system.

Run the GUI using one of the methods described in [Running the Software](#running-the-software).

The GUI loads the default `config_settings.yaml` and `colorspaces.yaml` on startup to populate the initial values. You can then modify these settings before generating the config.

### General Settings Tab
![screenshot_2025-04-06_14-36-16](https://github.com/user-attachments/assets/7e04759a-475b-4e60-8ea9-acd9da4a069d)

This tab mirrors most options found in the `settings` section of `config_settings.yaml`.

*   **Config Name:** Sets the `config_name`.
*   **Config Description:** Sets the `config_description` (multi-line text input).
*   **OCIO Version:** Selects the target `ocio_version_major` (1 or 2). Affects availability of subsequent options.
*   **Use Shortnames:** Toggles the `use_shortnames` setting. Changes how colorspace names are displayed in other parts of the GUI and in the final config.
*   **Enable Descriptions:** Toggles the `enable_descriptions` setting.
*   **Verbose Descriptions:** Toggles the `verbose_descriptions` setting (only enabled if "Enable Descriptions" is checked).
*   **Enable Built-in Transforms (OCIOv2):** Toggles the `enable_builtins` setting (only enabled if OCIO Version is 2).
*   **Enable Colorspace Encoding (OCIOv2):** Toggles the `enable_colorspace_encoding` setting (only enabled if OCIO Version is 2).
*   **Enable Colorspace Aliases (OCIOv2):** Toggles the `enable_colorspace_aliases` setting (only enabled if OCIO Version is 2).
*   **SPI1D LUT Precision (2^n):** Sets the `spi1d_lut_precision` using a spinbox (8-16).
*   **Category Folder Names:** Allows editing the mapping between colorspace categories (`work`, `camera`, `display`, `image`) and the desired folder/family names for applications.

### Colorspaces & Roles Tab
![screenshot_2025-04-06_14-36-24](https://github.com/user-attachments/assets/03a9bcb8-cb3f-4e79-8773-94309291cb7c)

This tab manages the selection of active colorspaces and the assignment of colorspaces to OCIO roles.

*   **Reference Colorspace (Scene-Linear):** A dropdown list to select the `reference_colorspace`. The list is filtered to only show colorspaces defined with `encoding: scene-linear` in `colorspaces.yaml`.
*   **Active Colorspaces:**
    *   **Listbox:** Displays all available colorspaces (based on `colorspaces.yaml`). Use Ctrl+Click or Shift+Click to select multiple colorspaces to include in the final config. The names displayed respect the "Use Shortnames" setting.
    *   **Select All / Deselect All Buttons:** Select or deselect all colorspaces in the list.
    *   **Ctrl+A / Cmd+A:** Toggles the selection of all items in the listbox.
*   **Roles Configuration (Treeview):**
    *   Displays the OCIO roles loaded initially from `config_settings.yaml`.
    *   **Columns:**
        *   `Role Name`: The name of the OCIO role (e.g., `scene_linear`, `color_timing`).
        *   `Assigned Colorspace`: The colorspace currently assigned to this role.
    *   **Editing:**
        *   Double-click a `Role Name` cell to edit the role name (must be unique, no spaces).
        *   Double-click an `Assigned Colorspace` cell to select a colorspace from a dropdown list of all *active* colorspaces.
    *   **Reordering:** Click and drag rows to change the order in which roles are defined in the final config.
    *   **Adding:** Click "Add Role" to create a new role row (you will be prompted for a name).
    *   **Deleting:** Select one or more rows and click "Delete Selected Role(s)" or press the `Delete` key.

### View Transforms Tab
![screenshot_2025-04-06_14-36-51](https://github.com/user-attachments/assets/c94b4eee-0e1c-4a62-951e-bfe41ca52889)

This tab handles the discovery, configuration, and mutation of view transforms based on LUT files.

*   **LUT Search Path:** Specify the directory containing the view transform LUT files (`.cube`, `.spi3d`, `.3dl`, etc.). Use the "Browse..." button to select a directory.
*   **LUT Filename Pattern:** Define the pattern (excluding extension) used to parse `viewName`, `displaySpace`, and optionally `shaperSpace` from LUT filenames (e.g., `{viewName}__{shaperSpace}_to_{displaySpace}`).
*   **Refresh Discovered LUTs:** Click this button to scan the "LUT Search Path" using the "LUT Filename Pattern". The treeview below will be populated with discovered LUTs and any default mutations based on the rules in the initially loaded `config_settings.yaml`.
*   **View Transforms Treeview:**
    *   Displays discovered LUTs and user-added mutations.
    *   **Columns:**
        *   `Type`: Indicates if the row represents a `LUT` or a `Mutated` view.
        *   `Source`: For `LUT` type, shows the original LUT filename. For `Mutated` type, shows which view/display it was mutated from.
        *   `View Name`: The parsed or manually entered view name (e.g., "OpenDRT v1.0.0 Default").
        *   `Shaper Space`: The parsed or manually selected shaper space (must be a log-encoded colorspace or a role resolving to one). Can be empty if the pattern doesn't include `{shaperSpace}`.
        *   `Display Space`: The parsed or manually selected display colorspace (must have `category: display`).
        *   `Status`: Shows the validation status (`OK`, `OK (Mutated Default)`, `OK (Mutated User)`, `Manual Entry Required`, or specific error messages).
    *   **Editing:** Double-click cells in the `View Name`, `Shaper Space`, or `Display Space` columns to edit their values. `Shaper Space` and `Display Space` provide dropdowns filtered to valid options (log spaces/roles for shaper, display spaces for display). `View Name` is a text entry. Editing is restricted for `Mutated` rows (View/Shaper cannot be changed).
    *   **Validation:** Edits trigger automatic validation. Rows with errors (e.g., invalid shaper, inactive display) are highlighted in red. Tooltips on status cells may provide more error details.
    *   **Reordering:** Click and drag rows to change the order of views within their respective displays in the final config.
    *   **Context Menu (Right-Click):**
        *   `Mutate Selected View(s)...`: Available if one or more valid `LUT` rows are selected. Prompts for a target display and adds new `Mutated` rows to the list for that display, based on the selected LUT(s).
        *   `Delete Selected View(s)`: Available if any rows are selected. Deletes the selected rows (LUTs or Mutations) from the list.
    *   **Delete Key:** Deletes the selected row(s).

### Bottom Controls

Located at the bottom of the main window.

*   **Output Directory:** Specify the parent directory where the final config folder (containing the `.ocio` file and LUTs) will be created. Use "Browse..." to select.
*   **Generate Config:** Click this button to start the OCIO config generation process using all the settings configured in the GUI. It performs validation checks before proceeding.
*   **Status Bar:** Displays messages about the current state or the outcome of operations (e.g., "Ready.", "Discovering LUTs...", "Config generated successfully...", "Error...").
*   **Dark Mode:** Toggles the GUI theme between dark and light modes.

---

## Configuration Files (YAML)

OCIOGen relies on two primary YAML files for its configuration: `config_settings.yaml` and `colorspaces.yaml`.

### `config_settings.yaml`

This file contains the main settings for the config generation process, including global options, role definitions, active colorspace lists, and view transform discovery rules.

```yaml
settings:
  # ... global settings ...
  view_transform_settings:
    # ... view transform specific settings ...
  view_mutate:
    # ... view mutation rules ...

roles:
  # ... role definitions ...

active_colorspaces:
  # ... list of active colorspace shortnames ...

colorspaces: !include colorspaces.yaml
```

#### `settings`

This section defines global parameters for the generated OCIO config.

*   `config_name` (String): The base name for the generated OCIO config file and the directory containing it and its associated LUTs.
    *   Example: `OpenDRT_v1.0.0_full-config`
*   `config_description` (String): A description embedded within the generated OCIO config file.
    *   Example: `"An OCIO config generated with ociogen."`
*   `config_location` (String): The parent directory where the config folder (named using `config_name`) will be created. Supports `~` for the user's home directory.
    *   Example: `/path/to/your/ocio/configs/` or `~/ocio_configs`
*   `ocio_version_major` (Integer): Specifies the target major OCIO version (either `1` or `2`). This affects available features and syntax.
    *   Example: `1`
*   `use_shortnames` (Boolean): If `true`, use the `shortname` attribute from `colorspaces.yaml` as the colorspace name in the OCIO config where available. If `false` or `shortname` is missing, use the full `name`.
    *   Example: `false`
*   `enable_descriptions` (Boolean): If `true`, include the `description` field for each colorspace in the generated config.
    *   Example: `false`
*   `verbose_descriptions` (Boolean): If `true` (and `enable_descriptions` is `true`), use the full description from `colorspaces.yaml`. If `false`, use the colorspace's full `name` as the description.
    *   Example: `false`
*   `enable_builtins` (Boolean): **(OCIOv2 only)** If `true`, use OCIOv2 built-in mathematical transforms (like `LogCameraTransform`, `ExponentWithLinearTransform`) defined in `tf_builtin` in `colorspaces.yaml` instead of generating `.spi1d` LUTs from Python `tf` functions. **Use with caution**, as built-ins can be significantly less precise than high-resolution LUTs.
    *   Example: `false`
*   `enable_colorspace_encoding` (Boolean): **(OCIOv2 only)** If `true`, include the `encoding` attribute (e.g., `scene-linear`, `log`, `sdr-video`) for colorspaces in the generated config.
    *   Example: `false`
*   `enable_colorspace_aliases` (Boolean): **(OCIOv2 only)** If `true`, include the `aliases` attribute for colorspaces, using the `alias` field from `colorspaces.yaml`.
    *   Example: `false`
*   `spi1d_lut_precision` (Integer): Defines the precision for generated 1D LUTs (`.spi1d`) used for transfer functions. The LUT size will be 2<sup>n</sup>. A value of `13` results in 8192 entries.
    *   Example: `13`
*   `reference_colorspace` (String): The `name` or `shortname` of the colorspace to be used as the central reference space (typically a scene-linear space). This gamut is what all other colorspaces calculate their matrices in reference to. Uses a YAML anchor (`&ref_lin`) for re-use in roles.
    *   Example: `&ref_lin filmlight-egamut2-lin`
*   `reference_log_colorspace` (String): The `name` or `shortname` of the primary log colorspace, often used for roles like `color_timing`. Uses a YAML anchor (`&ref_log`).
    *   Example: `&ref_log filmlight-egamut2-tlog`
*   `category_folder_names` (List of Dictionaries): Maps colorspace `category` values (from `colorspaces.yaml`) to folder names (Families) used in applications like Nuke.
    *   Example:
        ```yaml
        category_folder_names:
          - work: Working Spaces
          - camera: Camera Spaces
          - display: Display Spaces
          - image: Image Formation # Category for generated view transforms
        ```
*   `view_transform_settings` (Dictionary): Contains settings related to view transform LUT discovery.
    *   `lut_search_path` (String): The directory path (absolute or relative to `ociogen.py`) where view transform LUTs are located.
        *   Example: `/path/to/luts/` or `../shared_luts`
    *   `lut_filename_pattern` (String): A pattern used to parse information from LUT filenames (excluding the extension). Use placeholders `{viewName}`, `{displaySpace}`, and optionally `{shaperSpace}`. Underscores in the matched `{viewName}` part will be replaced with spaces.
        *   Example: `"{viewName}__{shaperSpace}_to_{displaySpace}"`
*   `view_mutate` (Dictionary): Defines rules for automatically generating additional view transforms for target displays based on LUTs found for a source display. The keys are source display `shortname`s, and the values are lists of target display `shortname`s. If a value is `null` or missing (like `display-p3:`), it means no targets are defined for that source. Use an empty list `[]` to explicitly define no targets.
    *   Example:
        ```yaml
        view_mutate:
          rec1886:
            - srgb-display
          display-p3: [] # Explicitly no targets for Display P3
        ```

#### `roles`

This section defines the standard OCIO roles and assigns a default colorspace (`name` or `shortname`) to each. The `reference` role is set automatically based on the `reference_colorspace` setting and should not be defined here. YAML anchors (`*ref_lin`, `*ref_log`) can be used to reference the colorspaces defined in the `settings` section.

*   Example:
    ```yaml
    roles:
      scene_linear: *ref_lin
      color_timing: *ref_log
      compositing_log: *ref_log
      # ... other roles
    ```

#### `active_colorspaces`

This is a list of colorspace `shortname`s (must match the `shortname` field in `colorspaces.yaml`). Only colorspaces whose `shortname` appears in this list will be included in the generated OCIO config. If this list is missing or empty in the YAML, *all* colorspaces defined in `colorspaces.yaml` will be considered active (this behaviour might differ slightly between CLI and GUI initial load).

*   Example:
    ```yaml
    active_colorspaces:
      - bypass
      - xyz-d65
      - aces-ap0
      - acescg
      # ... other shortnames
    ```

#### `colorspaces`

This key uses the special `!include` tag provided by the custom `IncludeLoader` to load the colorspace definitions from a separate file, typically `colorspaces.yaml`.

*   Example:
    ```yaml
    colorspaces: !include colorspaces.yaml
    ```

### `colorspaces.yaml`

This file contains a list of colorspace definitions. Each item in the list is a dictionary defining the properties of a single colorspace.

*   **`name`** (String, Required): The full, descriptive name of the colorspace.
    *   Example: `"Filmlight E-Gamut / T-Log"`
*   **`shortname`** (String, Required): A concise, often filesystem-friendly name used for identification in `active_colorspaces` and potentially in the final OCIO config if `use_shortnames` is `true`. **Must be unique.**
    *   Example: `"filmlight-egamut-tlog"`
*   **`category`** (String, Optional): A category for organizing colorspaces (e.g., `work`, `camera`, `display`, `image`). Used by `category_folder_names` in `config_settings.yaml`.
    *   Example: `"camera"`
*   **`alias`** (String, Optional): **(OCIOv2 only)** An alternative, often very short, name for the colorspace. Used if `enable_colorspace_aliases` is `true`.
    *   Example: `"tlog"`
*   **`description`** (String, Optional): A textual description of the colorspace. Used if `enable_descriptions` is `true`. Can be multi-line.
    *   Example: `"Log encoding curve for Filmlight E-Gamut."`
*   **`encoding`** (String, Optional): **(OCIOv2 only)** Specifies the encoding type. Used if `enable_colorspace_encoding` is `true`. Valid values: `scene-linear`, `log`, `sdr-video`, `hdr-video`, `data`.
    *   Example: `"log"`
*   **`chr`** (List or String, Optional): Defines the chromaticity coordinates (gamut).
    *   **List:** A list of 8 float values representing the xy coordinates of Red, Green, Blue, and White points `[Rx, Ry, Gx, Gy, Bx, By, Wx, Wy]`. A matrix transform to the reference space will be calculated.
        *   Example: `[0.7347, 0.2653, 0.0000, 1.0986, 0.0001, -0.0987, 0.32168, 0.33767]`
    *   **String:** The `name` or `shortname` of *another* colorspace defined in this file. This indicates that the current colorspace shares the same primaries as the referenced one. A `ColorSpaceTransform` will be generated between the referenced space and the reference role.
        *   Example: `"aces-ap0"` (meaning this space uses ACES AP0 primaries)
*   **`tf`** (String, Optional): The name of a Python transfer function defined in `utilities/transfer_functions.py`. An `.spi1d` LUT will be generated based on this function. The function name should ideally contain `oetf` (Optical to Electrical Transfer Function: usually for inverse/to_linear LUTs) or `eotf`/`eocf` (Electrical to Optical Transfer Function: usually for forward/from_linear LUTs) to guide the LUT generation direction.
    *   Example: `"oetf_arri_logc3"`
*   **`tf_builtin`** (Dictionary, Optional): **(OCIOv2 only)** Defines an OCIOv2 built-in mathematical transform to use instead of a Python function LUT (if `enable_builtins` is `true`).
    *   `type` (String): The type of OCIO transform (e.g., `LogCameraTransform`, `ExponentWithLinearTransform`, `LogAffineTransform`, `ExponentTransform`, `BuiltinTransform`).
    *   `params` (Dictionary): Parameters for the specified transform type, using snake_case keys (they will be converted to camelCase for OCIO). Refer to OCIO documentation for available parameters for each type.
        *   Example:
            ```yaml
            tf_builtin:
              type: LogCameraTransform
              params:
                lin_side_break: 0.010591
                log_side_slope: 0.247190
                # ... other params ...
                direction: inverse # 'forward' or 'inverse'
            ```
*   **`forward`** (Boolean, Optional): Defines the primary direction of the transform group relative to the reference space. `true` means TO_REFERENCE, `false` means FROM_REFERENCE. Defaults to `true` if omitted. This affects the order of operations when multiple transforms (gamut + transfer function) are present.
    *   Example: `true`

---

## Command-Line Usage (`ociogen.py`)

You can generate an OCIO configuration directly from the command line by running the `ociogen.py` script.

```bash
python ociogen.py
```

When run this way:

1.  It automatically looks for `config_settings.yaml` in the same directory as the script.
2.  It reads all settings, roles, active colorspaces, and includes `colorspaces.yaml`.
3.  It performs LUT discovery based on the `view_transform_settings` in `config_settings.yaml`.
    *   If LUT parsing fails for required components (display, shaper if needed) and the script is run interactively (with a TTY), it will prompt the user to enter the correct colorspace name or role. If run non-interactively, it will skip the problematic LUT.
4.  It applies view mutations based on the `view_mutate` rules in `config_settings.yaml`.
5.  It generates the OCIO config file and associated LUTs inside a folder specified by `config_location` and `config_name` within `config_settings.yaml`.

Currently, there are no command-line arguments to override the default `config_settings.yaml` path or other settings. All configuration is done via the YAML files when using the script directly.

---

