import os
import sys
import shutil
import argparse
from pathlib import Path
import importlib.resources

from .utilities import transfer_functions
from .gui import main as run_gui 
from .core import OCIOConfig


def localize_configs(scope='config'):
    """Copies default config.yaml and optionally colorspaces.yaml to the CWD."""
    print(f"Attempting to localize default configuration files (scope: {scope})...")
    data_pkg_ref = importlib.resources.files('ociogen.data')
    cwd = Path(os.getcwd())
    if scope == 'all':
        files_to_copy = ['config.yaml', 'colorspaces.yaml']
    elif scope == 'config':
        files_to_copy = ['config.yaml']
    else:
        print(f"Error: Invalid localization scope '{scope}'. Use 'config' or 'all'.")
        return # Or raise an error
    copied_count = 0
    skipped_count = 0

    for filename in files_to_copy:
        source_filename = 'config.yaml' if filename == 'config.yaml' else filename
        source_path_ref = data_pkg_ref.joinpath(source_filename)
        # Destination path uses the target filename (e.g., config.yaml)
        dest_path = cwd / filename

        if not source_path_ref.is_file():
            print(f"Warning: Default file '{source_filename}' not found in package data. Cannot localize.")
            continue

        if dest_path.exists():
            print(f"Warning: '{dest_path.name}' already exists in the current directory. Skipping.") # Use dest_path.name
            skipped_count += 1
        else:
            try:
                shutil.copy2(str(source_path_ref), str(dest_path)) # copy2 preserves metadata
                print(f"Copied default '{source_filename}' to '{dest_path.name}'.") # Use dest_path.name
                copied_count += 1
            except Exception as e:
                print(f"Error copying default '{source_filename}' to '{dest_path.name}': {e}") # Use dest_path.name

    if copied_count > 0:
        print(f"Localization complete. Copied {copied_count} file(s).")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} file(s) as they already exist.")
    if copied_count == 0 and skipped_count == 0:
         print("No files were localized (defaults might be missing from package data).")


def main():
    """Entry point for the command-line tool or GUI."""
    # If no arguments are provided, launch the GUI
    if len(sys.argv) == 1:
        print("No arguments provided, launching GUI...")
        run_gui()
        sys.exit(0)

    parser = argparse.ArgumentParser(
        description="Generate an OCIO configuration or manage configuration files.",
        prog='ociogen' # Set the program name for help messages
    )
    subparsers = parser.add_subparsers(dest='command', help='Available sub-commands')

    # --- Run Command ---
    parser_run = subparsers.add_parser('run', help='Generate the OCIO config using settings from config.yaml')
    parser_run.add_argument(
        '--config',
        type=str,
        metavar='PATH',
        help="Path to a specific config.yaml file to use (overrides default search order)."
    )
    parser_run.add_argument(
        '--output',
        type=str,
        metavar='DIR',
        help="Directory where the generated config folder will be placed (overrides config.yaml)."
    )

    # --- Localize Command ---
    parser_localize = subparsers.add_parser('localize', help='Copy default config files to the current directory.')
    parser_localize.add_argument(
        'scope',
        nargs='?', # Makes the argument optional
        choices=['config', 'all'],
        default='config', # Default value if argument is omitted
        help="Specify which files to copy: 'config' (default: config.yaml only) or 'all' (config.yaml and colorspaces.yaml)."
    )

    # --- Parse Arguments ---
    # sys.argv[1:] contains the arguments passed to the script
    args = parser.parse_args(sys.argv[1:])


    if args.command == 'localize':
        localize_configs(scope=args.scope) # Pass the scope argument
        sys.exit(0)

    elif args.command == 'run':
        print("Starting OCIO config generation (run command)...")
        config_settings_path = args.config # Will be None if not provided
        output_dir = args.output # Will be None if not provided

        try:
            # Instantiate OCIOConfig (now imported from core), passing paths
            ocio_config_instance = OCIOConfig(config_settings_path=config_settings_path, output_dir=output_dir)
            ocio_config_instance.create_config() # Call the method on the instance
        except Exception as e:
            print(f"\nAn error occurred during config generation: {e}", file=sys.stderr)
            # Consider adding traceback for debugging
            # import traceback
            # traceback.print_exc()
            sys.exit(1)
    elif args.command is None:
        # This case should ideally not be reached if GUI launch works,
        # but it's good practice to handle it.
        # It might be reached if only 'ociogen' is typed with no args,
        # and the len(sys.argv) check fails for some reason.
        # Or if a user types 'ociogen --help' without a subcommand.
        # The argparse library handles --help automatically.
        # If other args are passed without a subcommand, argparse shows an error.
        # If no command but other args, argparse should show help/error.
        # If truly no command and no args, the GUI should have launched.
        # So, we can just print the help here as a fallback.
        parser.print_help(sys.stderr)
        sys.exit(1)


# Entry point for script execution
if __name__ == "__main__":
    main()

