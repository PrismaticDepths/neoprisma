#! /usr/bin/env bash

setopt SH_WORD_SPLIT
set -euo pipefail
exec 3</dev/tty

while true; do
	printf "This installer will build/compile Neoprisma locally and install it. Python >= 3.10 is recommended. Proceed? [y/n] " > /dev/tty
	read -r yn < /dev/tty
	case $yn in
		[Yy]* ) echo "Installing..."; break;; # Break the loop and continue script
		[Nn]* ) echo "Exiting..."; exit;; # Exit the script
		* ) echo "Please answer yes or no.";; # Loop back for invalid input
	esac
done

LOG_FILE=$(mktemp /tmp/neoprisma_installer.XXXX)

run_step() {
	local msg="$1"
    shift
    printf "  [..] %s" "$msg"

	if "$@" > "$LOG_FILE" 2>&1; then
		printf "\r  [\033[32mOK\033[0m] %s\n" "$msg"
	else
		printf "\r  [\033[31mFAIL\033[0m] %s\n" "$msg"
		cat "$LOG_FILE"
		exit 1
	fi
}

run_step_permissive() {
	local msg="$1"
    shift
    printf "  [..] %s" "$msg"

	if "$@" > "$LOG_FILE" 2>&1; then
		printf "\r  [\033[32mOK\033[0m] %s\n" "$msg"
	else
		printf "\r  [\033[33mWARN\033[0m] %s\n" "$msg"
		cat "$LOG_FILE"
	fi
}

BUILD_DIR="$HOME/.neoprisma-build"
INSTALL_DIR="$HOME/Applications"
APP_NAME="neoprisma"
BUNDLE_ID="com.prismaticdepths.neoprisma"
BRANCH="stable"
OPTIND=1

while getopts ":b:i:r:" opt; do
	case "$opt" in
		b)
			echo "Using BUILD_DIR $OPTARG"
			BUILD_DIR="$OPTARG"
			;;
		i)
			echo "Using INSTALL_DIR $OPTARG"
			INSTALL_DIR="$OPTARG"
			;;
		r)
			echo "Using BRANCH $OPTARG"
			BRANCH="$OPTARG"
			;;
		\?)
			echo "Invalid option. Usage:
curl -fsSL https://raw.githubusercontent.com/PrismaticDepths/neoprisma/stable/install.sh | $SHELL -s -- [-r BRANCH] [-b BUILD_DIR] [-i INSTALL_DIR]" >&2
			exit 1
			;;
		:)
			echo "Option -$OPTARG requires an argument" >&2
			exit 1
			;;
	esac
done

if [ "$#" -gt 0 ]; then
	while true; do
		printf "The installer was invoked with flags that can modify its behaviour. Install anyways? [y/n] " > /dev/tty
		read -r yn < /dev/tty
		case $yn in
			[Yy]* ) break;; # Break the loop and continue script
			[Nn]* ) echo "Exiting..."; exit;; # Exit the script
			* ) echo "Please answer yes or no.";; # Loop back for invalid input
		esac
	done
fi

echo -n "  [..] Checking OS and arch"

die() {
	echo "$*" >&2
	exit 1
}

version_ge() {
	[ "$(printf '%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

# OS check
[[ "$(uname)" == "Darwin" ]] || die "\r  [\033[31mFAIL\033[0m] Checking OS and arch\nERROR: invalid OS (must be on macOS)"

# macOS version check
REQUIRED_MACOS="12.0"
INSTALLED_MACOS=$(sw_vers -productVersion)

version_ge "$INSTALLED_MACOS" "$REQUIRED_MACOS" \
	|| die "\r  [\033[31mFAIL\033[0m] Checking OS and arch\nERROR: macOS $REQUIRED_MACOS+ required (found $INSTALLED_MACOS)"

# Architecture check
ARCH=$(uname -m)
[[ "$ARCH" == "arm64" || "$ARCH" == "x86_64" ]] \
	|| die "\r  [\033[31mFAIL\033[0m] Checking OS and arch\nERROR: unsupported CPU architecture $ARCH (must be arm64 or x86_64)"

echo "\r  [\033[32mOK\033[0m] Checking OS and arch"

echo -n "  [..] Checking for dependencies"

require_cmd() {
	command -v "$1" >/dev/null 2>&1 || die "\r  [\033[31mFAIL\033[0m] Checking for dependencies\nERROR: missing dependency $1"
}

require_cmd git
require_cmd python3
require_cmd clang++

echo "\r  [\033[32mOK\033[0m] Checking for dependencies"

if [ -d "$BUILD_DIR" ]; then
	if [[ -n "$BUILD_DIR" ]] && [[ "$BUILD_DIR" != "$HOME" ]] && [[ "$BUILD_DIR" != "/" ]]; then
		while true; do
			printf "The given BUILD_DIR ($BUILD_DIR) exists and is not empty. Delete it and install here anyways? [y/n] " > /dev/tty
			read -r yn < /dev/tty
			case $yn in
				[Yy]* ) break;; # Break the loop and continue script
				[Nn]* ) echo "Stopping installer..."; exit;; # Exit the script
				* ) echo "Please answer yes or no.";; # Loop back for invalid input
			esac
		done
		rm -rf "$BUILD_DIR"
	else
		die "BUILD_DIR is empty or home. Installing to those locations is unsafe."
	fi
fi

if [ -d "$INSTALL_DIR/$APP_NAME.app" ]; then
	if [[ -n "$INSTALL_DIR/$APP_NAME.app" ]] && [[ "$INSTALL_DIR/$APP_NAME.app" != "$HOME" ]] && [[ "$INSTALL_DIR/$APP_NAME.app" != "/" ]]; then
		while true; do
			printf "Neoprisma is already installed in the target location ($INSTALL_DIR/$APP_NAME.app). If you are updating the app, this is normal. Replace the existing app and proceed with installation? [y/n] " > /dev/tty
			read -r yn < /dev/tty
			case $yn in
				[Yy]* ) break;; # Break the loop and continue script
				[Nn]* ) echo "Stopping installer..."; exit;; # Exit the script
				* ) echo "Please answer yes or no.";; # Loop back for invalid input
			esac
		done
		run_step_permissive "Resetting Accessibility approval status for $BUNDLE_ID" tccutil reset Accessibility "$BUNDLE_ID" 
		run_step_permissive "Resetting ListenEvent approval status for $BUNDLE_ID" tccutil reset ListenEvent "$BUNDLE_ID"
		rm -rf "$INSTALL_DIR/$APP_NAME.app"
	else
		die "INSTALL_DIR/APP_NAME.app is empty or home. Installing to those locations is unsafe."
	fi
fi 

if python3 -c "import sys; sys.exit(0) if sys.version_info >= (3,10) else sys.exit(1)"; then
	echo "  [\033[32mOK\033[0m] Python install: $(python3 --version)"
else
	echo "  [\033[31mFAIL\033[0m] Python 3.10+ required (found $(python3 --version)) "
	echo "         ↳ See https://python.org/downloads for information"
	exit 1
fi

echo "Fetching source..."

run_step "Cloning repo into build dir" git clone -b "$BRANCH" https://github.com/PrismaticDepths/neoprisma "$BUILD_DIR"

cd "$BUILD_DIR"

LATEST_VERSION="${$(curl -s "https://api.github.com/repos/PrismaticDepths/neoprisma/releases/latest" | \
    grep '"tag_name":' | \
    sed -E 's/.*"([^"]+)".*/\1/'):-}" || true

if [[ -z "$LATEST_VERSION" ]]; then
    echo "  [\033[33mWARN\033[0m] Failed to fetch latest version, defaulting to '0.0.1'"
    LATEST_VERSION="0.0.1"
else
	echo "  [\033[32mOK\033[0m] Latest release version: $LATEST_VERSION"
fi


cat <<EOF > src/version.py
__version__ = "$LATEST_VERSION"
EOF


echo "Installing Python dependencies... "

python3 -m venv .venv
source .venv/bin/activate
PIP="python3 -m pip"
run_step "Installing pip" $PIP install --upgrade pip
run_step "Installing from requirements.txt" $PIP install -r requirements.txt
run_step "Installing pyinstaller" $PIP install pyinstaller 
cd src

PYTHON_EXE=$(which python3 || which python)
EXT_SUFFIX=$($PYTHON_EXE -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")

echo "Building from source... "

run_step "Building binaries" clang++ -arch $ARCH -O3 -Wall -shared -std=c++17 -undefined dynamic_lookup $($PYTHON_EXE -m pybind11 --includes) playback.cpp -o playback$EXT_SUFFIX automation_macos.cpp

cd ..

PLAYBACK_FILE=(src/playback*"${EXT_SUFFIX}")

run_step "Building application bundle" $PYTHON_EXE -m PyInstaller \
	--windowed \
	--name "$APP_NAME" \
	--icon "src/assets/ico-dark.icns" \
	--osx-bundle-identifier "$BUNDLE_ID" \
	--add-data "src:src" \
	--add-data "src/assets/Credits.rtf:." \
	--add-data "src/assets:assets" \
	--add-binary "${PLAYBACK_FILE}:src" \
	--hidden-import=Quartz \
	--hidden-import=Quartz.CoreGraphics \
	--hidden-import=Quartz.CoreText \
	--hidden-import=Cocoa \
	--hidden-import=ApplicationServices \
	src/main.py

echo "Finalizing... "

mkdir -p "$INSTALL_DIR"
run_step "Moving dist to installation dir" mv "$BUILD_DIR/dist/$APP_NAME.app" "$INSTALL_DIR/"

ENTITLEMENTS="$BUILD_DIR/entitlements.plist"
generate_entitlements_tmp() {
cat > "$ENTITLEMENTS" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
	<dict>
	<key>com.apple.security.cs.disable-library-validation</key>
	<true/>

	<key>com.apple.security.cs.allow-jit</key>
	<true/>

	<key>com.apple.security.cs.allow-unsigned-executable-memory</key>
	<true/>

	<key>com.apple.security.accessibility</key>
	<true/>

	<key>com.apple.security.device.keyboard</key>
	<true/>

	<key>com.apple.security.device.mouse</key>
	<true/>
</dict>
</plist>
EOF
}

fix_plist() {
PLIST_PATH="$INSTALL_DIR/$APP_NAME.app/Contents/Info.plist" # (probably)
plutil -replace NSHumanReadableCopyright -string "© 2026 PrismaticDepths" "$PLIST_PATH"
plutil -replace CFBundleShortVersionString -string "$LATEST_VERSION" "$PLIST_PATH"
plutil -replace CFBundleIdentifier -string "$BUNDLE_ID" "$PLIST_PATH"
}

run_step "Generating Info.plist" fix_plist
run_step "Generating entitlements.plist" generate_entitlements_tmp
run_step "Signing app" codesign --force --deep --sign - --options runtime  --entitlements "$ENTITLEMENTS" "$INSTALL_DIR/$APP_NAME.app" 

echo "Cleaning up... "
if [ -d "$BUILD_DIR" ]; then
	if [[ -n "$BUILD_DIR" ]] && [[ "$BUILD_DIR" != "$HOME" ]] && [[ "$BUILD_DIR" != "/" ]]; then
		rm -rf "$BUILD_DIR"
	else
		die "BUILD_DIR is empty or home. Cannot clean. The app has still been installed."
	fi
fi

echo "\033[32mInstallation complete!\033[0m Remember to grant the app Accessibility & Input Monitoring permissions, even if you just reinstalled or updated the app."
