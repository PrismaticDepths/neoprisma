#! /usr/bin/env bash

set -euo pipefail
exec 3</dev/tty

while true; do
	read -r -u 3 -p "This program will install Neoprisma. Proceed with installation? [y/n] " yn < /dev/tty
	case $yn in
		[Yy]* ) echo "Installing..."; break;; # Break the loop and continue script
		[Nn]* ) echo "Exiting..."; exit;; # Exit the script
		* ) echo "Please answer yes or no.";; # Loop back for invalid input
	esac
done

BUILD_DIR="$HOME/.neoprisma-build"
INSTALL_DIR="$HOME/Applications"
APP_NAME="neoprisma"
BUNDLE_ID="com.prismaticdepths.neoprisma"

die() {
	echo "ERROR: $*" >&2
	exit 1
}

version_ge() {
	[ "$(printf '%s\n' "$2" "$1" | sort -V | head -n1)" = "$2" ]
}

# OS check
[[ "$(uname)" == "Darwin" ]] || die "invalid OS (must be on macOS)"

# macOS version check
REQUIRED_MACOS="12.0"
INSTALLED_MACOS=$(sw_vers -productVersion)

version_ge "$INSTALLED_MACOS" "$REQUIRED_MACOS" \
	|| die "macOS $REQUIRED_MACOS+ required (found $INSTALLED_MACOS)"

# Architecture check
ARCH=$(uname -m)
[[ "$ARCH" == "arm64" || "$ARCH" == "x86_64" ]] \
	|| die "unsupported CPU architecture $ARCH (must be arm64 or x86_64)"

require_cmd() {
	command -v "$1" >/dev/null 2>&1 || die "missing dependency $1"
}

require_cmd git
require_cmd python3
require_cmd clang++


if [ -d "$BUILD_DIR" ]; then

	if [[ -n "$BUILD_DIR" ]] && [[ "$BUILD_DIR" != "$HOME" ]] && [[ "$BUILD_DIR" != "/" ]]; then
		while true; do
			read -r -u 3 -p "The given BUILD_DIR ($BUILD_DIR) exists and is not empty. Delete it and install here anyways? [y/n] " yn < /dev/tty
			case $yn in
				[Yy]* ) echo "Continuing..."; break;; # Break the loop and continue script
				[Nn]* ) echo "Stopping installer..."; exit;; # Exit the script
				* ) echo "Please answer yes or no.";; # Loop back for invalid input
			esac
		done
		rm -rf "$BUILD_DIR"
	else
		die "BUILD_DIR is empty or home. Installing to those locations is unsafe."
	fi
fi

git clone https://github.com/PrismaticDepths/neoprisma "$BUILD_DIR"
cd "$BUILD_DIR"

python3 -m venv .venv
source .venv/bin/activate
PIP="python3 -m pip"
$PIP install --upgrade pip
$PIP install -r requirements.txt
$PIP install pyinstaller
cd src
clang++ -O3 -Wall -shared -std=c++17 -undefined dynamic_lookup $(python3 -m pybind11 --includes) playback.cpp -o playback$(python3-config --extension-suffix)

cd ..

pyinstaller \
	--windowed \
	--name "$APP_NAME" \
	--osx-bundle-identifier "$BUNDLE_ID" \
	--add-data "src:src" \
	--add-data "src/assets:assets" \
	--add-binary "src/playback*$(python3-config --extension-suffix):src" \
	--hidden-import=Quartz \
	src/main.py

mkdir -p "$INSTALL_DIR"

mv "$BUILD_DIR/dist/$APP_NAME.app" "$INSTALL_DIR/"
codesign --force --deep --sign - "$INSTALL_DIR/$APP_NAME.app"

echo "Installed dist at $INSTALL_DIR/$APP_NAME.app"
if [ -d "$BUILD_DIR" ]; then

	if [[ -n "$BUILD_DIR" ]] && [[ "$BUILD_DIR" != "$HOME" ]] && [[ "$BUILD_DIR" != "/" ]]; then
		while true; do
			read -r -u 3 -p "Clean up BUILD_DIR ($BUILD_DIR)? [y/n] " yn < /dev/tty
			case $yn in
				[Yy]* ) echo "Cleaning..."; break;; # Break the loop and continue script
				[Nn]* ) echo "Exiting..."; exit;; # Exit the script
				* ) echo "Please answer yes or no.";; # Loop back for invalid input
			esac
		done
		rm -rf "$BUILD_DIR"
	else
		die "BUILD_DIR is empty or home. Cannot clean."
	fi
fi
echo "Installation complete!"