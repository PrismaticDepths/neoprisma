#! /usr/bin/env bash

if [ -n "$ZSH_VERSION" ]; then
  setopt SH_WORD_SPLIT
fi
set -euo pipefail


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

INTERACTIVE=1
BUILD_DIR="$HOME/.neoprisma-build"
ENTITLEMENTS="$BUILD_DIR/entitlements.plist"
INSTALL_DIR="/Applications"
APP_NAME="neoprisma"
BUNDLE_ID="com.prismaticdepths.neoprisma"
BRANCH="stable"
FROM_SOURCE=0
WELCOME_MESSAGE="download and install the latest available Neoprisma release"
OPTIND=1

while getopts ":b:i:r:y:s:" opt; do
	case "$opt" in
		b)
			echo "Using BUILD_DIR $OPTARG"
			BUILD_DIR="$OPTARG"
			ENTITLEMENTS="$BUILD_DIR/entitlements.plist"
			;;
		i)
			echo "Using INSTALL_DIR $OPTARG"
			INSTALL_DIR="$OPTARG"
			;;
		r)
			echo "Using BRANCH $OPTARG"
			BRANCH="$OPTARG"
			;;
		y)  if [ "$OPTARG" != "NO"]; then
				echo "(NOTICE) Running in NON-INTERACTIVE mode: All prompts will be automatically accepted"
				INTERACTIVE=0
			fi
			;;
		s)  if [ "$OPTARG" != "NO"]; then
				echo "Building from source"
				FROM_SOURCE=1
				WELCOME_MESSAGE="build/compile Neoprisma locally and install it. Python >= 3.10 is recommended"
			fi
			;;
		\?)
			echo "Invalid option. (Note-All options are... optional.) Usage:
curl -fsSL https://raw.githubusercontent.com/PrismaticDepths/neoprisma/stable/install.sh | $SHELL -s -- [-r BRANCH] [-b BUILD_DIR] [-i INSTALL_DIR] [-s YES/NO] [-y YES/NO]" >&2
			exit 1
			;;
		:)	
			if [[ "$OPTARG"!="s" ]]; then
				echo "Option -$OPTARG requires an argument" >&2
				exit 1
			fi
			;;
	esac
done

if [ "$#" -gt 0 ]; then
	printf "(NOTICE) This installer is running with flags that can modify its behaviour. See above for details."
fi

if [ "$INTERACTIVE" = 1 ]; then
	exec 3</dev/tty
	while true; do
		printf "This installer will $WELCOME_MESSAGE. Proceed? [y/n] " > /dev/tty
		read -r yn < /dev/tty
		case $yn in
			[Yy]* ) echo "Installing..."; break;; # Break the loop and continue script
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

generate_entitlements() {
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

if [ -d "$BUILD_DIR" ]; then
	if [[ -n "$BUILD_DIR" ]] && [[ "$BUILD_DIR" != "$HOME" ]] && [[ "$BUILD_DIR" != "/" ]]; then
		if [ "$INTERACTIVE" = 1 ]; then
			while true; do
				printf "The given BUILD_DIR ($BUILD_DIR) exists and is not empty. Delete it and install here anyways? [y/n] " > /dev/tty
				read -r yn < /dev/tty
				case $yn in
					[Yy]* ) break;; # Break the loop and continue script
					[Nn]* ) echo "Stopping installer..."; exit;; # Exit the script
					* ) echo "Please answer yes or no.";; # Loop back for invalid input
				esac
			done
		fi
		rm -rf "$BUILD_DIR"
	else
		die "BUILD_DIR is empty or home. Installing to those locations is unsafe."
	fi
fi

run_step_permissive "Resetting Accessibility approval status for $BUNDLE_ID" tccutil reset Accessibility "$BUNDLE_ID" 
run_step_permissive "Resetting ListenEvent approval status for $BUNDLE_ID" tccutil reset ListenEvent "$BUNDLE_ID"

if [ -d "$INSTALL_DIR/$APP_NAME.app" ]; then
	if [[ -n "$INSTALL_DIR/$APP_NAME.app" ]] && [[ "$INSTALL_DIR/$APP_NAME.app" != "$HOME" ]] && [[ "$INSTALL_DIR/$APP_NAME.app" != "/" ]]; then
		if [ "$INTERACTIVE" = 1 ]; then
			while true; do
				printf "Neoprisma is already installed in the target location ($INSTALL_DIR/$APP_NAME.app). If you are updating the app, this is normal. Replace the existing app and proceed with installation? [y/n] " > /dev/tty
				read -r yn < /dev/tty
				case $yn in
					[Yy]* ) break;; # Break the loop and continue script
					[Nn]* ) echo "Stopping installer..."; exit;; # Exit the script
					* ) echo "Please answer yes or no.";; # Loop back for invalid input
				esac
			done
		fi
		rm -rf "$INSTALL_DIR/$APP_NAME.app"
	else
		die "INSTALL_DIR/APP_NAME.app is empty or home. Installing to those locations is unsafe."
	fi
fi 

if [ "$FROM_SOURCE" -eq 0 ]; then
	TAG_NAME=$(curl -s "https://api.github.com/repos/PrismaticDepths/neoprisma/releases/latest" | \
		grep '"tag_name":' | \
		sed -E 's/.*"([^"]+)".*/\1/')
	LATEST_VERSION="${TAG_NAME:-}"
	if [[ -z "$LATEST_VERSION" ]]; then
		echo "  [\033[31mWARN\033[0m] Failed to fetch latest version."
		exit 1
	else
		echo "  [\033[32mOK\033[0m] Latest release version: $LATEST_VERSION"
	fi
	BUNDLE_URL="https://github.com/PrismaticDepths/neoprisma/releases/download/${LATEST_VERSION}/neoprisma-macos.tar.xz"
	if curl --head --fail "$BUNDLE_URL" >/dev/null 2>&1; then
		mkdir -p "$BUILD_DIR"
		mkdir -p "$INSTALL_DIR"
		mkdir -p "$BUILD_DIR/extract"
		echo "Precompiled bundle found. Skipping build stage and using the bundle instead..."
		run_step "Downloading precompiled bundle" curl -L "$BUNDLE_URL" -o "$BUILD_DIR/neoprisma.tar.xz"
		run_step "Extracting precompiled bundle" tar -xJf "$BUILD_DIR/neoprisma.tar.xz" -C "$BUILD_DIR/extract"
		EXTRACTED_APP=$(find "$BUILD_DIR/extract" -maxdepth 1 -name "*.app" -type d | head -n 1)
		echo "Finalizing..."
		run_step "Moving app to $INSTALL_DIR" mv "$EXTRACTED_APP" "$INSTALL_DIR/$APP_NAME.app"
		run_step "Generating entitlements.plist" generate_entitlements
		run_step "Signing app" codesign --force --deep --sign - --options runtime  --entitlements "$ENTITLEMENTS" "$INSTALL_DIR/$APP_NAME.app" 
		echo "Cleaning up... "
		if [ -d "$BUILD_DIR" ]; then
			if [[ -n "$BUILD_DIR" ]] && [[ "$BUILD_DIR" != "$HOME" ]] && [[ "$BUILD_DIR" != "/" ]]; then
				rm -rf "$BUILD_DIR"
			else
				die "BUILD_DIR is empty or home. Cannot clean. The app has still been installed."
			fi
		fi
		echo -e "\033[32mInstallation complete! Neoprisma has been installed at $INSTALL_DIR/$APP_NAME.app\n--> Caveats: \033[0m You must grant the app Accessibility & Input Monitoring permissions, even if you just reinstalled or updated the app."
		exit 0
	else
		echo "No precompiled bundle found, or the -s flag was passed. Building from source."
	fi
fi

echo -n "  [..] Checking for dependencies"

require_cmd() {
	command -v "$1" >/dev/null 2>&1 || die "\r  [\033[31mFAIL\033[0m] Checking for dependencies\nERROR: missing dependency $1"
}

require_cmd git
require_cmd python3
require_cmd clang++

echo "\r  [\033[32mOK\033[0m] Checking for dependencies"

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

TAG_NAME=$(curl -s "https://api.github.com/repos/PrismaticDepths/neoprisma/releases/latest" | \
	grep '"tag_name":' | \
	sed -E 's/.*"([^"]+)".*/\1/')
LATEST_VERSION="${TAG_NAME:-}"

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
	--icon "src/assets/AppIcon.icns" \
	--osx-bundle-identifier "$BUNDLE_ID" \
	--add-data "src:src" \
	--add-data "src/assets/Assets.car:." \
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



fix_plist() {
PLIST_PATH="$INSTALL_DIR/$APP_NAME.app/Contents/Info.plist" # (probably)
plutil -replace NSHumanReadableCopyright -string "© 2026 PrismaticDepths" "$PLIST_PATH"
plutil -replace CFBundleShortVersionString -string "$LATEST_VERSION" "$PLIST_PATH"
plutil -replace CFBundleIdentifier -string "$BUNDLE_ID" "$PLIST_PATH"
plutil -replace CFBundleIconName -string "AppIcon" "$PLIST_PATH"
plutil -replace LSUIElement -bool true "$PLIST_PATH"
plutil -replace NSRequiresAquaSystemAppearance -bool false "$PLIST_PATH"
}

run_step "Generating Info.plist" fix_plist
run_step "Generating entitlements.plist" generate_entitlements
run_step "Signing app" codesign --force --deep --sign - --options runtime  --entitlements "$ENTITLEMENTS" "$INSTALL_DIR/$APP_NAME.app" 

echo "Cleaning up... "
if [ -d "$BUILD_DIR" ]; then
	if [[ -n "$BUILD_DIR" ]] && [[ "$BUILD_DIR" != "$HOME" ]] && [[ "$BUILD_DIR" != "/" ]]; then
		rm -rf "$BUILD_DIR"
	else
		die "BUILD_DIR is empty or home. Cannot clean. The app has still been installed."
	fi
fi

echo -e "\033[32mInstallation complete! Neoprisma has been installed at $INSTALL_DIR/$APP_NAME.app\n--> Caveats: \033[0m You must grant the app Accessibility & Input Monitoring permissions, even if you just reinstalled or updated the app."
