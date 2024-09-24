#!/bin/bash

# 0. Determine the directory of the script itself
script_dir=$(dirname "$(realpath "$0")")

# 1. Set default ISO URL and ISO path, can be overridden by environment variables or script arguments
iso=${iso:-"https://ftp.iij.ad.jp/pub/linux/rocky/\$version/isos/x86_64/Rocky-x86_64-dvd.iso"}
iso_path=${iso_path:-"$script_dir/isos/Rocky-x86_64-dvd.iso"}

# 2. Check if the script is running on a compatible platform (el8 or later)
release_info=$(grep -E '^VERSION_ID|^PLATFORM_ID' /etc/os-release)

# Extract platform and version information
platform=$(echo "$release_info" | grep 'PLATFORM_ID' | cut -d= -f2 | tr -d '"')
version=$(echo "$release_info" | grep 'VERSION_ID' | cut -d= -f2 | tr -d '"')

# Check if the platform is el8 or later
if [[ "$platform" != "platform:el8" && "$platform" != "platform:el9" ]]; then
    echo "Error: This script can only be run on platform:el8 or later."
    exit 1
fi

echo "Running on a compatible platform: $platform (Version: $version)"

# Display version and release information
version=$(echo $release_info | grep -oP '\d+' | head -1)
release=$(echo $release_info | grep -oP '\d+\.\d+')

# 3. Check if qemu-kvm kernel module is loaded
if ! lsmod | grep -q kvm; then
    echo "Error: KVM kernel module is not loaded. Please load the module and try again."
    exit 1
fi

# 4. Check if required packages are installed
for pkg in qemu-kvm lorax; do
    if ! rpm -q $pkg &>/dev/null; then
        echo "Error: The package $pkg is not installed. Please install it and rerun the script."
        exit 1
    fi
done

# 5. Check if the ISO image exists, and if not, download it
if [ ! -f "$iso_path" ]; then
    echo "ISO file does not exist. Downloading..."

    # URL with dynamic version
    iso_url=$(echo $iso | sed "s/\\\$version/$version/g")

    # Download the ISO
    wget -O "$iso_path" "$iso_url"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to download the ISO file."
        exit 1
    fi
    echo "ISO file downloaded: $iso_path"
else
    echo "ISO file already exists: $iso_path"
fi

# results_dir and tmp cleanup if they exist
if [ -d "$script_dir/build-iso" ]; then
    echo "Cleaning up existing results directory..."
    rm -rf "$script_dir/build-iso"
fi

if [ -d "$script_dir/tmp" ]; then
    echo "Cleaning up temporary files (only the contents)..."
    rm -rf "$script_dir/tmp"/*
fi

# Check scripts dir
if [ ! -d "$script_dir/scripts" ]; then
    echo "Error: Source scripts directory $script_dir/scripts does not exist."
    exit 1
fi

# 6. Set default bootmode to mbr if not specified
bootmode=${bootmode:-"mbr"}
echo "Selected ISO boot mode: $bootmode"

# 7. Set kickstart file and additional options based on bootmode
if [ "$bootmode" == "uefi" ]; then
    ks_file="$script_dir/kickstart/uefi_main.ks"
    extra_opts="--virt-uefi"
elif [ "$bootmode" == "mbr" ]; then
    ks_file="$script_dir/kickstart/mbr_main.ks"
    extra_opts=""
else
    echo "Error: Invalid boot mode specified. Use 'uefi' or 'mbr'."
    exit 1
fi

# Run livemedia-creator (Required KVM)
sudo livemedia-creator \
  --make-iso \
  --ks="$ks_file" \
  --iso="$iso_path" \
  --iso-name="liveboot.iso" \
  --iso-only \
  --resultdir="$script_dir/build-iso" \
  --logfile="$script_dir/logs/livemedia-creator.log" \
  --project="Rocky Linux" \
  --releasever=$release \
  --tmp="$script_dir/tmp" \
  --image-size=8192 \
  --lorax-templates="$script_dir/tmpl" \
  $extra_opts

# Check the result of livemedia-creator
if [ $? -ne 0 ]; then
    echo "Error: livemedia-creator failed. Check the log for details: $script_dir/logs/livemedia-creator.log"
    exit 1
else
    echo "livemedia-creator completed successfully."
fi

echo "Create Bootable ISO completed. Only liveboot.iso remains in the build-iso directory."

