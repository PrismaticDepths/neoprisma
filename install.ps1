# install.ps1 - Neoprisma Windows Installer

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$LOG_FILE = Join-Path ($env:TEMP) ("neoprisma_installer_" + [guid]::NewGuid().ToString("N").Substring(0, 8) + ".log")
$ORIG_DIR = Get-Location

function Write-StepOk([string]$Message) {
    Write-Host "`r  [" -NoNewline
    Write-Host "OK" -ForegroundColor Green -NoNewline
    Write-Host "] $Message"
}

function Write-StepWarn([string]$Message) {
    Write-Host "`r  [" -NoNewline
    Write-Host "WARN" -ForegroundColor Yellow -NoNewline
    Write-Host "] $Message"
}

function Write-StepFail([string]$Message) {
    Write-Host "`r  [" -NoNewline
    Write-Host "FAIL" -ForegroundColor Red -NoNewline
    Write-Host "] $Message"
}

function Stop-WithError([string]$Message) {
    Write-Host "$Message" -ForegroundColor Red
    Set-Location "$ORIG_DIR"
    exit 1
}

function Invoke-Step {
    param(
        [string]$Message,
        [scriptblock]$Action
    )
    Write-Host -NoNewline "  [..] $Message"
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $global:LASTEXITCODE = 0
        & $Action > "$LOG_FILE" 2>&1
        $exitCode = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }
    } catch {
        $_ | Out-File -FilePath "$LOG_FILE" -Append -Encoding utf8
        $exitCode = 1
    } finally {
        $ErrorActionPreference = $prevEAP
    }

    if ($exitCode -eq 0) {
        Write-StepOk "$Message"
    } else {
        Write-StepFail "$Message"
        if (Test-Path "$LOG_FILE") {
            Get-Content "$LOG_FILE" | Out-Host
        }
        Set-Location "$ORIG_DIR"
        exit 1
    }
}

function Invoke-StepPermissive {
    param(
        [string]$Message,
        [scriptblock]$Action
    )
    Write-Host -NoNewline "  [..] $Message"
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $global:LASTEXITCODE = 0
        & $Action > "$LOG_FILE" 2>&1
        $exitCode = if ($null -ne $LASTEXITCODE) { $LASTEXITCODE } else { 0 }
    } catch {
        $_ | Out-File -FilePath "$LOG_FILE" -Append -Encoding utf8
        $exitCode = 1
    } finally {
        $ErrorActionPreference = $prevEAP
    }

    if ($exitCode -eq 0) {
        Write-StepOk "$Message"
    } else {
        Write-StepWarn "$Message"
        if (Test-Path "$LOG_FILE") {
            Get-Content "$LOG_FILE" | Out-Host
        }
    }
}

function Confirm-Prompt([string]$PromptText) {
    while ($true) {
        $yn = Read-Host -Prompt "$PromptText [y/n]"
        if ($yn -match '^[Yy]') { return $true }
        if ($yn -match '^[Nn]') { return $false }
        Write-Host "Please answer yes or no."
    }
}

# Defaults
$INTERACTIVE = 1
$BUILD_DIR = Join-Path ($env:USERPROFILE) ".neoprisma-build"
$INSTALL_DIR = Join-Path ($env:LOCALAPPDATA) "Programs"
$APP_NAME = "neoprisma"
$BRANCH = "stable"
$FROM_SOURCE = 0
$WELCOME_MESSAGE = "download and install the latest available Neoprisma release"
$ENABLE_SCRIPTING = "False"

# Parse CLI flags (-b, -i, -r, -y, -s) matching install.sh getopts
$argIndex = 0
while ($argIndex -lt $args.Count) {
    $opt = [string]$args[$argIndex]
    if ($opt -in @("-b", "-i", "-r", "-y", "-s")) {
        if (($argIndex + 1) -ge $args.Count -or ([string]$args[$argIndex + 1]).StartsWith("-")) {
            if ($opt -ne "-s") {
                Write-Error "Option $opt requires an argument"
                exit 1
            } else {
                $optArg = "YES"
                $argIndex += 1
            }
        } else {
            $optArg = [string]$args[$argIndex + 1]
            $argIndex += 2
        }

        switch -Exact ($opt) {
            "-b" {
                Write-Host "Using BUILD_DIR $optArg"
                $BUILD_DIR = $optArg
            }
            "-i" {
                Write-Host "Using INSTALL_DIR $optArg"
                $INSTALL_DIR = $optArg
            }
            "-r" {
                Write-Host "Using BRANCH $optArg"
                $BRANCH = $optArg
            }
            "-y" {
                if ($optArg -ne "NO") {
                    Write-Host "(NOTICE) Running in NON-INTERACTIVE mode: All prompts will be automatically accepted"
                    $INTERACTIVE = 0
                }
            }
            "-s" {
                if ($optArg -ne "NO") {
                    Write-Host "Building from source"
                    $FROM_SOURCE = 1
                    $WELCOME_MESSAGE = "build/compile Neoprisma locally and install it. Python >= 3.10 is recommended"
                }
            }
        }
    } else {
        Write-Host @"
Invalid option. (Note-All options are... optional.) Usage:
& ([scriptblock]::Create((irm https://raw.githubusercontent.com/PrismaticDepths/neoprisma/stable/install.ps1))) [-r BRANCH] [-b BUILD_DIR] [-i INSTALL_DIR] [-s YES/NO] [-y YES/NO]
"@ -ForegroundColor Red
        exit 1
    }
}

if ($args.Count -gt 0) {
    Write-Host "(NOTICE) This installer is running with flags that can modify its behaviour. See above for details."
}

if ($INTERACTIVE -eq 1) {
    if (Confirm-Prompt "This installer will $WELCOME_MESSAGE. Proceed?") {
        Write-Host "Installing..."
    } else {
        Write-Host "Exiting..."
        exit 0
    }
}

# OS and Architecture Check
Write-Host -NoNewline "  [..] Checking OS and arch"

if ($env:OS -ne "Windows_NT") {
    Write-StepFail "Checking OS and arch"
    Stop-WithError "ERROR: invalid OS (must be on Windows)"
}

$osVersion = [System.Environment]::OSVersion.Version
if ($osVersion.Major -lt 10) {
    Write-StepFail "Checking OS and arch"
    Stop-WithError "ERROR: Windows 10+ required (found $($osVersion.ToString()))"
}

$arch = $env:PROCESSOR_ARCHITECTURE
if ($arch -ne "AMD64" -and $arch -ne "ARM64") {
    Write-StepFail "Checking OS and arch"
    Stop-WithError "ERROR: unsupported CPU architecture $arch (must be AMD64 or ARM64)"
}

Write-StepOk "Checking OS and arch"

# Validate and clean BUILD_DIR
$rootDrive = [System.IO.Path]::GetPathRoot($BUILD_DIR)
if (Test-Path "$BUILD_DIR") {
    if (-not [string]::IsNullOrWhiteSpace($BUILD_DIR) -and ($BUILD_DIR -ne $env:USERPROFILE) -and ($BUILD_DIR -ne $rootDrive)) {
        if ($INTERACTIVE -eq 1) {
            if (-not (Confirm-Prompt "The given BUILD_DIR ($BUILD_DIR) exists and is not empty. Delete it and install here anyways?")) {
                Write-Host "Stopping installer..."
                exit 0
            }
        }
        Remove-Item -Recurse -Force "$BUILD_DIR" -ErrorAction Stop
    } else {
        Stop-WithError "BUILD_DIR is empty, root, or user home. Installing to those locations is unsafe."
    }
}

# Validate and clean target installation directory
$APP_TARGET_DIR = Join-Path "$INSTALL_DIR" "$APP_NAME"
$installRootDrive = [System.IO.Path]::GetPathRoot($APP_TARGET_DIR)
if (Test-Path "$APP_TARGET_DIR") {
    if (-not [string]::IsNullOrWhiteSpace($APP_TARGET_DIR) -and ($APP_TARGET_DIR -ne $env:USERPROFILE) -and ($APP_TARGET_DIR -ne $installRootDrive)) {
        if ($INTERACTIVE -eq 1) {
            if (-not (Confirm-Prompt "Neoprisma is already installed in the target location ($APP_TARGET_DIR). If you are updating the app, this is normal. Replace the existing app and proceed with installation?")) {
                Write-Host "Stopping installer..."
                exit 0
            }
        }
        Get-Process -Name "$APP_NAME" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force "$APP_TARGET_DIR" -ErrorAction Stop
    } else {
        Stop-WithError "INSTALL_DIR/APP_NAME is empty, root, or user home. Installing to those locations is unsafe."
    }
}

# Helper for creating Desktop and Start Menu shortcuts
function New-AppShortcut([string]$ShortcutPath, [string]$TargetExe, [string]$WorkingDir, [string]$IconFile) {
    $wshShell = New-Object -ComObject WScript.Shell
    $shortcut = $wshShell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $TargetExe
    $shortcut.WorkingDirectory = $WorkingDir
    if (Test-Path "$IconFile") {
        $shortcut.IconLocation = "$IconFile,0"
    } else {
        $shortcut.IconLocation = "$TargetExe,0"
    }
    $shortcut.Save()
}

if ($FROM_SOURCE -eq 0) {
    $LATEST_VERSION = $null
    try {
        $releaseInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/PrismaticDepths/neoprisma/releases/latest" -Headers @{ "User-Agent" = "neoprisma-installer" } -ErrorAction Stop
        $LATEST_VERSION = $releaseInfo.tag_name
    } catch {
        $LATEST_VERSION = $null
    }

    if ([string]::IsNullOrWhiteSpace($LATEST_VERSION)) {
        Write-StepWarn "Failed to fetch latest version."
        Stop-WithError "ERROR: Could not determine latest release version."
    } else {
        Write-StepOk "Latest release version: $LATEST_VERSION"
    }

    $BUNDLE_URL = "https://github.com/PrismaticDepths/neoprisma/releases/download/$LATEST_VERSION/neoprisma-win32.tar.xz"
    
    # Check if the precompiled Windows archive exists on the release
    & curl.exe --head --fail "$BUNDLE_URL" >$null 2>&1
    if ($LASTEXITCODE -eq 0) {
        $EXTRACT_DIR = Join-Path "$BUILD_DIR" "extract"
        $BUNDLE_ARCHIVE = Join-Path "$BUILD_DIR" "neoprisma.tar.xz"

        New-Item -ItemType Directory -Path "$BUILD_DIR" -Force | Out-Null
        New-Item -ItemType Directory -Path "$INSTALL_DIR" -Force | Out-Null
        New-Item -ItemType Directory -Path "$EXTRACT_DIR" -Force | Out-Null

        Write-Host "Precompiled bundle found. Skipping build stage and using the bundle instead..."

        Invoke-Step "Downloading precompiled bundle" {
            & curl.exe -fL "$BUNDLE_URL" -o "$BUNDLE_ARCHIVE"
        }

        Invoke-Step "Extracting precompiled bundle" {
            & tar.exe -xJf "$BUNDLE_ARCHIVE" -C "$EXTRACT_DIR"
        }

        $EXTRACTED_APP = Join-Path "$EXTRACT_DIR" "$APP_NAME"
        if (-not (Test-Path "$EXTRACTED_APP")) {
            $firstDir = Get-ChildItem -Path "$EXTRACT_DIR" -Directory | Select-Object -First 1
            if ($firstDir) {
                $EXTRACTED_APP = $firstDir.FullName
            } else {
                Stop-WithError "ERROR: Extracted application directory not found in bundle."
            }
        }

        Write-Host "Finalizing..."

        Invoke-Step "Moving app to $INSTALL_DIR" {
            Move-Item -Path "$EXTRACTED_APP" -Destination "$APP_TARGET_DIR" -Force -ErrorAction Stop
        }

        $INSTALLED_EXE = Join-Path "$APP_TARGET_DIR" "$APP_NAME.exe"
        $INSTALLED_ICON = Join-Path "$APP_TARGET_DIR" "_internal\assets\AppIcon.ico"
        $START_MENU_SHORTCUT = Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs\Neoprisma.lnk"
        $DESKTOP_SHORTCUT = Join-Path ([Environment]::GetFolderPath("Desktop")) "Neoprisma.lnk"

        Invoke-Step "Creating Start Menu shortcut" {
            New-AppShortcut -ShortcutPath "$START_MENU_SHORTCUT" -TargetExe "$INSTALLED_EXE" -WorkingDir "$APP_TARGET_DIR" -IconFile "$INSTALLED_ICON"
        }

        Invoke-Step "Creating Desktop shortcut" {
            New-AppShortcut -ShortcutPath "$DESKTOP_SHORTCUT" -TargetExe "$INSTALLED_EXE" -WorkingDir "$APP_TARGET_DIR" -IconFile "$INSTALLED_ICON"
        }

        Write-Host "Cleaning up... "
        Set-Location "$ORIG_DIR"

        if (Test-Path "$BUILD_DIR") {
            if (-not [string]::IsNullOrWhiteSpace($BUILD_DIR) -and ($BUILD_DIR -ne $env:USERPROFILE) -and ($BUILD_DIR -ne $rootDrive)) {
                Remove-Item -Recurse -Force "$BUILD_DIR" -ErrorAction SilentlyContinue
            } else {
                Stop-WithError "BUILD_DIR is empty, root, or user home. Cannot clean. The app has still been installed."
            }
        }

        if (Test-Path "$LOG_FILE") {
            Remove-Item -Force "$LOG_FILE" -ErrorAction SilentlyContinue
        }

        Write-Host "Installation complete! Neoprisma has been installed at $APP_TARGET_DIR" -ForegroundColor Green
        Write-Host "Shortcuts have been added to your Desktop and Start Menu." -ForegroundColor Green
        exit 0
    } else {
        Write-Host "No precompiled bundle found, or the -s flag was passed. Building from source."
    }
}

function Update-SessionPath {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

function Resolve-PythonCommand {
    foreach ($cmd in @("python", "python3")) {
        $found = Get-Command "$cmd" -ErrorAction SilentlyContinue
        if ($found) {
            $verOut = & "$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $verOut) {
                return $cmd
            }
        }
    }
    return $null
}

function Get-PythonTargetArch([string]$PyCmd) {
    if (-not $PyCmd) { return "x64" }
    $plat = (& "$PyCmd" -c "import sysconfig; print(sysconfig.get_platform())" 2>$null)
    if ($plat) {
        $plat = $plat.Trim().ToLower()
        if ($plat -eq "win-arm64") { return "ARM64" }
        if ($plat -eq "win32") { return "Win32" }
    }
    return "x64"
}

function Get-VsInstallationPath {
    $vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    if (Test-Path "$vswhere") {
        $vsPath = & "$vswhere" -latest -products * -property installationPath 2>$null
        if (-not [string]::IsNullOrWhiteSpace($vsPath)) {
            return $vsPath.Trim()
        }
    }
    return $null
}

function Find-MsvcClExe([string]$TargetArch) {
    $vsPath = Get-VsInstallationPath
    if (-not $vsPath) { return $null }
    $msvcRoot = Join-Path "$vsPath" "VC\Tools\MSVC"
    if (-not (Test-Path "$msvcRoot")) { return $null }

    $targetFolder = if ($TargetArch -eq "ARM64") { "arm64" } elseif ($TargetArch -eq "Win32") { "x86" } else { "x64" }
    $clFiles = Get-ChildItem -Path "$msvcRoot" -Recurse -Filter "cl.exe" -ErrorAction SilentlyContinue |
        Where-Object { $_.DirectoryName -match "[\\/]$targetFolder$" }
    if ($clFiles) {
        return ($clFiles | Select-Object -Last 1).FullName
    }
    return $null
}

Write-Host -NoNewline "  [..] Checking for dependencies"

$detectedPy = Resolve-PythonCommand
$targetArch = Get-PythonTargetArch $detectedPy
$msvcComponent = if ($targetArch -eq "ARM64") {
    "Microsoft.VisualStudio.Component.VC.Tools.ARM64"
} else {
    "Microsoft.VisualStudio.Component.VC.Tools.x86.x64"
}

$missingDeps = @()
if (-not (Get-Command "git" -ErrorAction SilentlyContinue)) { $missingDeps += @{ Name = "git"; WingetId = "Git.Git" } }
if (-not $detectedPy) { $missingDeps += @{ Name = "python (>= 3.10)"; WingetId = "Python.Python.3.12" } }
if (-not (Get-Command "cmake" -ErrorAction SilentlyContinue)) { $missingDeps += @{ Name = "cmake"; WingetId = "Kitware.CMake" } }
if (-not (Find-MsvcClExe $targetArch)) {
    $missingDeps += @{
        Name = "Visual Studio C++ Compiler ($targetArch)"
        IsMsvc = $true
        Component = $msvcComponent
    }
}

if ($missingDeps.Count -gt 0) {
    Write-StepWarn "Checking for dependencies"
    $missingNames = ($missingDeps | ForEach-Object { $_.Name }) -join ", "
    Write-Host "  Missing build dependencies: $missingNames" -ForegroundColor Yellow

    $installDeps = $true
    if ($INTERACTIVE -eq 1) {
        $installDeps = Confirm-Prompt "Would you like the installer to automatically install the missing dependencies ($missingNames)?"
    }
    if ($installDeps) {
        foreach ($dep in $missingDeps) {
            if ($dep.IsMsvc) {
                if (Get-Command "winget" -ErrorAction SilentlyContinue) {
                    Invoke-Step "Installing Visual Studio C++ Build Tools (Triggers UAC prompt)..." {
                        # Run winget in an elevated child process so only this step prompts for admin rights
                        $wingetArgs = "install --id Microsoft.VisualStudio.2022.BuildTools -e --accept-source-agreements --accept-package-agreements --override `"--wait --passive --norestart --add Microsoft.VisualStudio.Workload.VCTools --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 --includeRecommended`""
                        $proc = Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"$env:ProgramFiles\Microsoft Desktop App Installer\winget.exe` $wingetArgs`" -ErrorAction SilentlyContinue; if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { winget $wingetArgs }" -Verb RunAs -PassThru -Wait
                        
                        # Fallback direct winget invocation if path lookup differs
                        if ($proc.ExitCode -ne 0) {
                            $proc2 = Start-Process winget.exe -ArgumentList$wingetArgs -Verb RunAs -PassThru -Wait
                            if ($proc2.ExitCode -ne 0) {
                                throw "Visual Studio installation exited with code $($proc2.ExitCode)"
                            }
                        }
                    }
                } else {
                    Stop-WithError "ERROR: Could not find winget. Please install Visual Studio C++ Build Tools manually from https://visualstudio.microsoft.com/visual-cpp-build-tools/"
                }
            } else {
                $depId = $dep.WingetId
                Invoke-Step "Installing $($dep.Name) via winget" {
                    winget install --id "$depId" -e --accept-source-agreements --accept-package-agreements
                }
            }
            Update-SessionPath
        }
    } else {
        Stop-WithError "ERROR: missing required dependencies ($missingNames)"
    }
} else {
    Write-StepOk "Checking for dependencies"
}

$PYTHON_CMD = Resolve-PythonCommand
if (-not $PYTHON_CMD) {
    Stop-WithError "ERROR: Python could not be found in PATH."
}

$pyVersionCheck = & "$PYTHON_CMD" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
$pyVersionStr = (& "$PYTHON_CMD" --version 2>&1) -join " "
if ($LASTEXITCODE -eq 0) {
    Write-StepOk "Python install: $pyVersionStr"
} else {
    Write-StepFail "Python 3.10+ required (found $pyVersionStr)"
    Write-Host "         -> See https://python.org/downloads for information"
    exit 1
}

Write-Host "Fetching source..."

Invoke-Step "Cloning repo into build dir" {
    git clone -b "$BRANCH" "https://github.com/PrismaticDepths/neoprisma" "$BUILD_DIR"
}

Set-Location "$BUILD_DIR"

$LATEST_VERSION = $null
try {
    $releaseInfo = Invoke-RestMethod -Uri "https://api.github.com/repos/PrismaticDepths/neoprisma/releases/latest" -Headers @{ "User-Agent" = "neoprisma-installer" } -ErrorAction Stop
    $LATEST_VERSION = $releaseInfo.tag_name
} catch {
    $LATEST_VERSION = $null
}

if ([string]::IsNullOrWhiteSpace($LATEST_VERSION)) {
    Write-StepWarn "Failed to fetch latest version, defaulting to '0.0.1'"
    $LATEST_VERSION = "0.0.1"
} else {
    Write-StepOk "Latest release version: $LATEST_VERSION"
}

$versionPyContent = @"
__version__ = "$LATEST_VERSION"
ext = {
	"scripting":$ENABLE_SCRIPTING
}
"@
[System.IO.File]::WriteAllText((Join-Path "$BUILD_DIR" "src\version.py"), $versionPyContent, [System.Text.UTF8Encoding]::new($false))

Write-Host "Installing Python dependencies... "

Invoke-Step "Creating Python virtual environment" {
    & "$PYTHON_CMD" -m venv .venv
}

$VENV_SCRIPTS = Join-Path "$BUILD_DIR" ".venv\Scripts"
$PYTHON_EXE = Join-Path "$VENV_SCRIPTS" "python.exe"

# Activate the virtual environment in PATH so CMake's execute_process finds the venv Python
$env:VIRTUAL_ENV = Join-Path "$BUILD_DIR" ".venv"
$env:Path = "$VENV_SCRIPTS;$env:Path"

Invoke-Step "Installing pip" {
    & "$PYTHON_EXE" -m pip install --upgrade pip
}
Invoke-Step "Installing from requirements.txt" {
    & "$PYTHON_EXE" -m pip install -r requirements.txt
}
Invoke-Step "Installing pybind11, ninja, pyinstaller, and pillow" {
    & "$PYTHON_EXE" -m pip install pybind11 ninja pyinstaller pillow
}

$EXT_SUFFIX = (& "$PYTHON_EXE" -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))").Trim()
$PYBIND11_CMAKE_DIR = (& "$PYTHON_EXE" -c "import pybind11; print(pybind11.get_cmake_dir())").Trim()
$CMAKE_ARCH = Get-PythonTargetArch $PYTHON_EXE

Write-Host "Building from source... "

# Patch CMakeLists.txt if the remote branch still contains the broken '/X' flag
$cmakeFile = Join-Path "$BUILD_DIR" "CMakeLists.txt"
if (Test-Path "$cmakeFile") {
    $cmakeContent = [System.IO.File]::ReadAllText($cmakeFile)
    $cmakeContent = $cmakeContent -replace 'add_compile_options\(/X\)', '# removed /X flag'
    [System.IO.File]::WriteAllText($cmakeFile, $cmakeContent, [System.Text.UTF8Encoding]::new($false))
}

New-Item -ItemType Directory -Path "build" -Force | Out-Null
Set-Location "build"

$vsPath = Get-VsInstallationPath
$vcvarsall = if ($vsPath) { Join-Path "$vsPath" "VC\Auxiliary\Build\vcvarsall.bat" } else { $null }
$vcvarsArch = if ($CMAKE_ARCH -eq "ARM64") { "arm64" } elseif ($CMAKE_ARCH -eq "Win32") { "x86" } else { "x64" }

# Use Ninja + vcvarsall.bat when available to bypass MSBuild VCTargetsPath issues on ARM64 / VS 2026
if ($vcvarsall -and (Test-Path "$vcvarsall")) {
    $buildBatch = Join-Path "$BUILD_DIR" "build\run_cmake_build.bat"
    $batchContent = @"
@echo off
call "$vcvarsall" $vcvarsArch
if errorlevel 1 exit /b %errorlevel%
cmake .. -G "Ninja" -DCMAKE_BUILD_TYPE=Release -Dpybind11_DIR="$PYBIND11_CMAKE_DIR" -DPython_EXECUTABLE="$PYTHON_EXE" -DPYTHON_EXECUTABLE="$PYTHON_EXE"
if errorlevel 1 exit /b %errorlevel%
cmake --build . --config Release
if errorlevel 1 exit /b %errorlevel%
"@
    [System.IO.File]::WriteAllText($buildBatch, $batchContent, [System.Text.Encoding]::ASCII)

    Invoke-Step "Configuring and compiling binaries ($CMAKE_ARCH)..." {
        cmd.exe /c "`"$buildBatch`""
    }
} else {
    Invoke-Step "Configuring build layout ($CMAKE_ARCH)..." {
        cmake .. -A "$CMAKE_ARCH" -Dpybind11_DIR="$PYBIND11_CMAKE_DIR" -DPython_EXECUTABLE="$PYTHON_EXE" -DPYTHON_EXECUTABLE="$PYTHON_EXE"
    }

    Invoke-Step "Compiling binaries..." {
        cmake --build . --config Release
    }
}

Set-Location "$BUILD_DIR"

# Locate compiled playback extension in src/ (with fallback to src/Release/ if CMakeLists wasn't updated)
$playbackMatch = Get-ChildItem -Path "src" -Filter "playback*$EXT_SUFFIX" -File -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $playbackMatch -and (Test-Path "src\Release")) {
    $releaseMatch = Get-ChildItem -Path "src\Release" -Filter "playback*$EXT_SUFFIX" -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($releaseMatch) {
        Move-Item -Path ($releaseMatch.FullName) -Destination "src\" -Force
        Remove-Item -Recurse -Force "src\Release" -ErrorAction SilentlyContinue
        $playbackMatch = Get-ChildItem -Path "src" -Filter "playback*$EXT_SUFFIX" -File | Select-Object -First 1
    }
}

if (-not $playbackMatch) {
    Stop-WithError "ERROR: Compiled playback extension (*$EXT_SUFFIX) not found in src/"
}

$PLAYBACK_FILE = $playbackMatch.FullName
Remove-Item -Recurse -Force "build" -ErrorAction Stop

# Prefer dedicated Windows icon src/assets/AppIcon.ico, fallback to src/assets/preview.png
$ICON_PATH = if (Test-Path "src\assets\AppIcon.ico") {
    "src\assets\AppIcon.ico"
} else {
    "src\assets\preview.png"
}

Invoke-Step "Building application bundle" {
    & "$PYTHON_EXE" -m PyInstaller `
        --onedir `
        --windowed `
        --name "$APP_NAME" `
        --icon "$ICON_PATH" `
        --add-data "src;src" `
        --add-data "src/assets/Credits.rtf;." `
        --add-data "src/assets;assets" `
        --add-binary "$PLAYBACK_FILE;src" `
        --hidden-import=lupa `
        --hidden-import=lupa.core `
        --hidden-import=lupa._lupa `
        --hidden-import=lupa.lua54 `
        --collect-data lupa `
        --collect-binaries lupa `
        src/main.py
}

Write-Host "Finalizing... "

if (-not (Test-Path "$INSTALL_DIR")) {
    New-Item -ItemType Directory -Path "$INSTALL_DIR" -Force | Out-Null
}

Invoke-Step "Moving dist to installation dir" {
    Move-Item -Path (Join-Path "$BUILD_DIR" "dist\$APP_NAME") -Destination "$APP_TARGET_DIR" -Force -ErrorAction Stop
}

$INSTALLED_EXE = Join-Path "$APP_TARGET_DIR" "$APP_NAME.exe"
$INSTALLED_ICON = Join-Path "$APP_TARGET_DIR" "_internal\assets\AppIcon.ico"
$START_MENU_SHORTCUT = Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs\Neoprisma.lnk"
$DESKTOP_SHORTCUT = Join-Path ([Environment]::GetFolderPath("Desktop")) "Neoprisma.lnk"

Invoke-Step "Creating Start Menu shortcut" {
    New-AppShortcut -ShortcutPath "$START_MENU_SHORTCUT" -TargetExe "$INSTALLED_EXE" -WorkingDir "$APP_TARGET_DIR" -IconFile "$INSTALLED_ICON"
}

Invoke-Step "Creating Desktop shortcut" {
    New-AppShortcut -ShortcutPath "$DESKTOP_SHORTCUT" -TargetExe "$INSTALLED_EXE" -WorkingDir "$APP_TARGET_DIR" -IconFile "$INSTALLED_ICON"
}

Write-Host "Cleaning up... "
Set-Location "$ORIG_DIR"

if (Test-Path "$BUILD_DIR") {
    if (-not [string]::IsNullOrWhiteSpace($BUILD_DIR) -and ($BUILD_DIR -ne$env:USERPROFILE) -and ($BUILD_DIR -ne$rootDrive)) {
        Remove-Item -Recurse -Force "$BUILD_DIR" -ErrorAction SilentlyContinue
    } else {
        Stop-WithError "BUILD_DIR is empty, root, or user home. Cannot clean. The app has still been installed."
    }
}

if (Test-Path "$LOG_FILE") {
    Remove-Item -Force "$LOG_FILE" -ErrorAction SilentlyContinue
}

Write-Host "Installation complete! Neoprisma has been installed at $APP_TARGET_DIR" -ForegroundColor Green
Write-Host "Shortcuts have been added to your Desktop and Start Menu." -ForegroundColor Green