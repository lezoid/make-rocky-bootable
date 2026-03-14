#!/usr/bin/env python3
"""
Rocky Linux Bootable ISO Builder
Based on build.sh with interactive menu and password input
Uses Jinja2 templating for kickstart file generation
"""

import argparse
import hashlib
import os
import sys
import subprocess
import getpass
import re
import tempfile
import shutil
from pathlib import Path

try:
    from jinja2 import Template
except ImportError:
    print("Error: jinja2 is not installed.")
    print("Please install it with: pip3 install jinja2")
    print("Or on Rocky Linux: dnf install python3-jinja2")
    sys.exit(1)


class ISOBuilder:
    ISO_URLS = {
        '8':  "https://ftp.iij.ad.jp/pub/linux/rocky/8/isos/x86_64/Rocky-8-latest-x86_64-dvd.iso",
        '9':  "https://ftp.iij.ad.jp/pub/linux/rocky/9/isos/x86_64/Rocky-9-latest-x86_64-dvd.iso",
        '10': "https://ftp.iij.ad.jp/pub/linux/rocky/10/isos/x86_64/Rocky-10-latest-x86_64-dvd.iso",
    }

    def __init__(self):
        self.script_dir = Path(__file__).parent.resolve()
        self.iso_url = None
        self.iso_path = None
        self.bootmode = None
        self.root_password = None
        self.platform = None
        self.version = None
        self.release = None
        self.target_version = None
        self.extra_user = None  # {'name': str, 'password': str, 'sudoer': bool}
        self.debug = False

    def display_banner(self):
        """Display welcome banner"""
        print("=" * 70)
        print("  Rocky Linux Bootable ISO Builder")
        print("=" * 70)
        print()

    def check_platform(self):
        """Check if running on compatible platform (el8 or later)"""
        print("[1/8] Checking platform compatibility...")

        try:
            with open('/etc/os-release', 'r') as f:
                content = f.read()

            platform_match = re.search(r'PLATFORM_ID="([^"]+)"', content)
            version_match = re.search(r'VERSION_ID="([^"]+)"', content)

            if not platform_match or not version_match:
                print("Error: Cannot determine platform information")
                sys.exit(1)

            self.platform = platform_match.group(1)
            self.version = version_match.group(1).split('.')[0]
            self.release = version_match.group(1)

            if self.platform not in ["platform:el8", "platform:el9", "platform:el10"]:
                print(f"Error: This script can only be run on platform:el8 or later.")
                print(f"Current platform: {self.platform}")
                sys.exit(1)

            print(f"✓ Running on compatible platform: {self.platform} (Version: {self.release})")
            print()

        except FileNotFoundError:
            print("Error: /etc/os-release not found")
            sys.exit(1)

    def check_kvm_module(self):
        """Check if KVM kernel module is loaded"""
        print("[2/8] Checking KVM module...")

        result = subprocess.run(['lsmod'], capture_output=True, text=True)
        if 'kvm' not in result.stdout:
            print("Error: KVM kernel module is not loaded.")
            print("Please load the module and try again.")
            sys.exit(1)

        print("✓ KVM kernel module is loaded")
        print()

    def check_required_packages(self):
        """Check if required packages are installed"""
        print("[3/8] Checking required packages...")

        required_packages = ['qemu-kvm', 'lorax', 'lorax-lmc-virt', 'wget', 'isomd5sum', 'syslinux-nonlinux']
        missing_packages = []

        for pkg in required_packages:
            result = subprocess.run(['rpm', '-q', pkg],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
            if result.returncode != 0:
                missing_packages.append(pkg)

        if missing_packages:
            print(f"Error: The following packages are not installed:")
            for pkg in missing_packages:
                print(f"  - {pkg}")
            print("\nPlease install them and rerun the script.")
            sys.exit(1)

        print("✓ All required packages are installed")
        print()

    def select_target_version(self):
        """Interactive target Rocky Linux version selection"""
        print("[4/8] Select target Rocky Linux version:")
        print()
        print("  1) Rocky Linux 8")
        print("  2) Rocky Linux 9")
        print("  3) Rocky Linux 10")
        print()

        version_map = {'1': '8', '2': '9', '3': '10'}

        while True:
            choice = input("Enter your choice (1-3): ").strip()
            if choice in version_map:
                self.target_version = version_map[choice]
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

        self.iso_url = self.ISO_URLS[self.target_version]
        iso_filename = f"Rocky-{self.target_version}-latest-x86_64-dvd.iso"
        self.iso_path = self.script_dir / "isos" / iso_filename

        print(f"✓ Target version: Rocky Linux {self.target_version}")
        print()

    def download_iso_if_needed(self):
        """Download ISO if it doesn't exist"""
        print("[5/8] Checking ISO file...")

        if self.iso_path.exists():
            print(f"✓ ISO file already exists: {self.iso_path}")
            print()
            if self.verify_checksum():
                return
            print("Deleting corrupted ISO and re-downloading...")
            self.iso_path.unlink(missing_ok=True)

        print("ISO file does not exist. Downloading...")

        # Create isos directory if it doesn't exist
        self.iso_path.parent.mkdir(parents=True, exist_ok=True)

        # Download using wget with resume support
        result = subprocess.run(['wget', '-c', '-P', str(self.iso_path.parent), self.iso_url])

        if result.returncode != 0:
            print("Error: Failed to download the ISO file.")
            sys.exit(1)

        print(f"✓ ISO file downloaded: {self.iso_path}")
        print()

        if not self.verify_checksum():
            print("Error: Downloaded ISO failed checksum verification.")
            self.iso_path.unlink(missing_ok=True)
            sys.exit(1)

    def verify_checksum(self):
        """Download and verify SHA256 checksum of the ISO file"""
        print("Verifying ISO checksum...")

        checksum_url = self.iso_url + ".CHECKSUM"
        checksum_path = self.iso_path.with_suffix('.iso.CHECKSUM')

        # Download CHECKSUM file
        result = subprocess.run(['wget', '-q', '-O', str(checksum_path), checksum_url])
        if result.returncode != 0:
            print("Warning: Failed to download CHECKSUM file. Skipping verification.")
            return

        # Parse expected SHA256 hash from CHECKSUM file
        # Format: "SHA256 (filename) = <hash>"
        checksum_text = checksum_path.read_text()
        iso_filename = self.iso_path.name
        expected_hash = None
        for line in checksum_text.splitlines():
            if 'SHA256' in line and iso_filename in line:
                match = re.search(r'=\s*([0-9a-fA-F]{64})', line)
                if match:
                    expected_hash = match.group(1).lower()
                    break

        checksum_path.unlink(missing_ok=True)

        if not expected_hash:
            print("Warning: SHA256 hash not found in CHECKSUM file. Skipping verification.")
            return

        # Compute SHA256 of downloaded ISO
        print("Computing SHA256 hash (this may take a moment)...")
        sha256 = hashlib.sha256()
        with open(self.iso_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                sha256.update(chunk)
        actual_hash = sha256.hexdigest()

        if actual_hash != expected_hash:
            print("Warning: Checksum mismatch! The ISO may be corrupted.")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual:   {actual_hash}")
            return False

        print("✓ Checksum verified successfully")
        print()
        return True

    def select_bootmode(self):
        """Interactive bootmode selection"""
        print("[6/8] Select boot mode:")
        print()
        gui_desc = "KDE Plasma" if self.target_version == '10' else "XFCE + RDP"
        print("  1) uefi      - UEFI boot (CLI only)")
        print("  2) mbr       - MBR/BIOS boot (CLI only)")
        print(f"  3) uefi_gui  - UEFI boot with GUI ({gui_desc})")
        print(f"  4) mbr_gui   - MBR/BIOS boot with GUI ({gui_desc})")
        print()

        bootmode_map = {
            '1': 'uefi',
            '2': 'mbr',
            '3': 'uefi_gui',
            '4': 'mbr_gui'
        }

        while True:
            choice = input("Enter your choice (1-4): ").strip()

            if choice in bootmode_map:
                self.bootmode = bootmode_map[choice]
                print(f"✓ Selected boot mode: {self.bootmode}")
                print()
                if self.target_version == '10' and self.bootmode in ['uefi_gui', 'mbr_gui']:
                    print("=" * 70)
                    print("  WARNING: Rocky 10 GUI is experimental")
                    print("  KDE Plasma has large dependencies and the resulting ISO")
                    print("  will be significantly larger than CLI builds.")
                    print("=" * 70)
                    print()
                break
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")

    def input_root_password(self):
        """Interactive root password input"""
        print("[7/8] Set root password:")
        print()
        print("Enter the root password for the bootable ISO.")
        print("Note: Password must not be empty.")
        print()

        while True:
            password1 = getpass.getpass("Enter password: ")

            if not password1:
                print("Error: Password cannot be empty. Please try again.")
                print()
                continue

            password2 = getpass.getpass("Confirm password: ")

            if password1 != password2:
                print("Error: Passwords do not match. Please try again.")
                print()
                continue

            self.root_password = password1
            print("✓ Root password set successfully")
            print()
            break

    def input_extra_user(self):
        """Optionally create a general user"""
        print("Create a general user? (y/N): ", end='', flush=True)
        if input().strip().lower() != 'y':
            print()
            return

        while True:
            username = input("Username: ").strip()
            if username:
                break
            print("Username cannot be empty.")

        while True:
            password1 = getpass.getpass("User password: ")
            if not password1:
                print("Password cannot be empty. Please try again.")
                continue
            password2 = getpass.getpass("Confirm password: ")
            if password1 != password2:
                print("Passwords do not match. Please try again.")
                continue
            break

        sudoer = input("Add to sudoers? (y/N): ").strip().lower() == 'y'

        disable_root_ssh = False
        if sudoer:
            disable_root_ssh = input("Disable root SSH login? (y/N): ").strip().lower() == 'y'

        self.extra_user = {
            'name': username,
            'password': password1,
            'sudoer': sudoer,
            'disable_root_ssh': disable_root_ssh,
        }
        print(f"✓ User '{username}' will be created{' (sudoer)' if sudoer else ''}{' (root SSH disabled)' if disable_root_ssh else ''}")
        print()

    def cleanup_directories(self):
        """Cleanup build-iso and tmp directories"""
        print("Cleaning up directories...")

        # Remove build-iso directory (may be owned by root from previous sudo run)
        build_iso_dir = self.script_dir / "build-iso"
        if build_iso_dir.exists():
            print(f"  Removing {build_iso_dir}")
            result = subprocess.run(['sudo', 'rm', '-rf', str(build_iso_dir)])
            if result.returncode != 0:
                print(f"Error: Failed to remove {build_iso_dir}")
                sys.exit(1)

        # Clean tmp directory contents (keep .gitkeep)
        # Use sudo because previous runs may have left root-owned files
        tmp_dir = self.script_dir / "tmp"
        if tmp_dir.exists():
            for item in tmp_dir.iterdir():
                if item.name != '.gitkeep':
                    result = subprocess.run(['sudo', 'rm', '-rf', str(item)])
                    if result.returncode != 0:
                        print(f"Error: Failed to remove {item}")
                        sys.exit(1)

        print("✓ Directories cleaned")

    def generate_kickstart_from_template(self):
        """Generate kickstart file from Jinja2 template"""
        template_path = self.script_dir / 'kickstart' / 'template.ks.j2'

        if not template_path.exists():
            print(f"Error: Template file not found: {template_path}")
            sys.exit(1)

        # Read template
        with open(template_path, 'r') as f:
            template = Template(f.read())

        # Determine parameters
        is_uefi = self.bootmode in ['uefi', 'uefi_gui']
        is_gui = self.bootmode in ['uefi_gui', 'mbr_gui']

        # Render template
        kickstart_content = template.render(
            uefi=is_uefi,
            gui=is_gui,
            root_password=self.root_password,
            version=int(self.target_version),
            extra_user=self.extra_user,
            debug=self.debug
        )

        # Create temporary file
        tmp_dir = self.script_dir / 'tmp'
        tmp_dir.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(suffix='.ks', prefix='generated_',
                                         dir=tmp_dir)

        with os.fdopen(fd, 'w') as f:
            f.write(kickstart_content)

        if self.debug:
            print("=" * 70)
            print("  [DEBUG] Generated kickstart content:")
            print("=" * 70)
            for i, line in enumerate(kickstart_content.splitlines(), 1):
                print(f"{i:4}: {line}")
            print("=" * 70)
            print()

        return temp_path

    def build_iso(self):
        """Build the ISO using livemedia-creator"""
        print("[8/8] Building ISO image...")
        print()

        # Check scripts directory
        scripts_dir = self.script_dir / "scripts"
        if not scripts_dir.exists():
            print(f"Error: Source scripts directory {scripts_dir} does not exist.")
            sys.exit(1)

        # Set kickstart file and options based on bootmode
        bootmode_config = {
            'uefi': {
                'ks_file': 'kickstart/uefi_main.ks',
                'extra_opts': ['--virt-uefi'],
                'iso_name': f'Rocky-{self.target_version}-liveboot-uefi-x86_64.iso'
            },
            'mbr': {
                'ks_file': 'kickstart/mbr_main.ks',
                'extra_opts': [],
                'iso_name': f'Rocky-{self.target_version}-liveboot-mbr-x86_64.iso'
            },
            'uefi_gui': {
                'ks_file': 'kickstart/uefi_gui.ks',
                'extra_opts': ['--virt-uefi'],
                'iso_name': f'Rocky-{self.target_version}-liveboot-uefi_gui-x86_64.iso'
            },
            'mbr_gui': {
                'ks_file': 'kickstart/mbr_gui.ks',
                'extra_opts': [],
                'iso_name': f'Rocky-{self.target_version}-liveboot-mbr_gui-x86_64.iso'
            }
        }

        config = bootmode_config[self.bootmode]

        # Check if output ISO already exists
        output_iso = self.script_dir / 'build-iso' / config['iso_name']
        if output_iso.exists():
            answer = input(f"'{config['iso_name']}' already exists. Overwrite? (y/N): ").strip().lower()
            if answer != 'y':
                print("Aborted.")
                sys.exit(0)

        # Generate kickstart from template
        print("Generating kickstart file from template...")
        temp_ks = self.generate_kickstart_from_template()

        try:
            # Prepare livemedia-creator command
            cmd = [
                'sudo', 'livemedia-creator',
                '--make-iso',
                f'--ks={temp_ks}',
                f'--iso={self.iso_path}',
                f'--iso-name={config["iso_name"]}',
                '--iso-only',
                f'--resultdir={self.script_dir}/build-iso',
                f'--logfile={self.script_dir}/logs/livemedia-creator.log',
                '--project=Rocky Linux',
                f'--releasever={self.target_version}',
                f'--tmp={self.script_dir}/tmp',
                '--image-size=8704',
                f'--lorax-templates={self.script_dir}/tmpl'
            ]

            # Add extra options
            cmd.extend(config['extra_opts'])


            print("Running livemedia-creator (this may take a while)...")
            print(f"Log file: {self.script_dir}/logs/livemedia-creator.log")
            print()

            # Run livemedia-creator
            result = subprocess.run(cmd)

            if result.returncode != 0:
                print()
                print("Error: livemedia-creator failed.")
                print(f"Check the log for details: {self.script_dir}/logs/livemedia-creator.log")
                sys.exit(1)

            # Embed ISO checksum for "Test this media" boot option
            output_iso = self.script_dir / 'build-iso' / config['iso_name']
            print("Embedding ISO checksum (implantisomd5)...")
            checksum_result = subprocess.run(
                ['sudo', 'implantisomd5', '--force', str(output_iso)]
            )
            if checksum_result.returncode != 0:
                print("Warning: implantisomd5 failed. 'Test this media' may not work correctly.")

            print()
            print("=" * 70)
            print("✓ ISO creation completed successfully!")
            print("=" * 70)
            print()
            print(f"ISO file: {self.script_dir}/build-iso/{config['iso_name']}")
            print(f"Boot mode: {self.bootmode}")
            print()
            print("SECURITY REMINDER:")
            print("  - The ISO uses the custom root password you provided")
            print("  - SSH root login is enabled")
            print("  - SELinux is in permissive mode")
            print("  - This ISO is intended for temporary use only")
            print()

        finally:
            # Clean up temporary kickstart file
            if os.path.exists(temp_ks):
                os.unlink(temp_ks)

    def run(self):
        """Main execution flow"""
        try:
            self.display_banner()
            self.check_platform()
            self.check_kvm_module()
            self.check_required_packages()
            self.select_target_version()
            self.download_iso_if_needed()
            self.select_bootmode()
            self.input_root_password()
            self.input_extra_user()
            self.cleanup_directories()
            self.build_iso()

        except KeyboardInterrupt:
            print()
            print()
            print("Operation cancelled by user.")
            sys.exit(1)
        except Exception as e:
            print()
            print(f"Unexpected error: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Rocky Linux Bootable ISO Builder')
    parser.add_argument('--debug', action='store_true',
                        help='Debug mode: preserve logs inside the ISO')
    args = parser.parse_args()

    if os.geteuid() == 0:
        print("Warning: This script should not be run as root initially.")
        print("It will request sudo privileges when needed (for livemedia-creator).")
        print()
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            sys.exit(0)

    builder = ISOBuilder()
    builder.debug = args.debug
    builder.run()


if __name__ == "__main__":
    main()
