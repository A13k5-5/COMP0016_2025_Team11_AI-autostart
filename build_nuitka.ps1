param(
    [string]$ProjectRoot = $PSScriptRoot,
    [string]$VenvName = ".venv_build"
)

$ErrorActionPreference = "Stop"

function Assert-PathExists {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Label
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Label not found: $Path"
    }
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed ($LASTEXITCODE): $FilePath $($Arguments -join ' ')"
    }
}

function Resolve-PythonCommand {
    $candidates = @("python3.12")
    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $command) {
            return $candidate
        }
    }
    throw "Python launcher not found. Install Python and ensure 'py' or 'python' is available in PATH."
}

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$runScript = Join-Path $ProjectRoot "run_system_tray.py"
$requirements = Join-Path $ProjectRoot "requirements.txt"
$intelSource = Join-Path $ProjectRoot "src\video_recogniser\person_recogniser\intel"
$distDir = Join-Path $ProjectRoot "run_system_tray.dist"
$venvDir = Join-Path $ProjectRoot $VenvName
$venvPython = Join-Path $venvDir "Scripts\python.exe"

Assert-PathExists -Path $runScript -Label "Entry script"
Assert-PathExists -Path $requirements -Label "Requirements file"
Assert-PathExists -Path $intelSource -Label "Intel model folder"

Write-Host "[1/6] Creating clean virtual environment: $venvDir"
if (Test-Path -LiteralPath $venvDir) {
    Remove-Item -LiteralPath $venvDir -Recurse -Force
}

$pythonCommand = Resolve-PythonCommand
if ($pythonCommand -eq "py") {
    Invoke-CheckedCommand -FilePath $pythonCommand -Arguments @("-3", "-m", "venv", $venvDir)
} else {
    Invoke-CheckedCommand -FilePath $pythonCommand -Arguments @("-m", "venv", $venvDir)
}
Assert-PathExists -Path $venvPython -Label "Virtual environment python"

Write-Host "[2/6] Installing dependencies and Nuitka 4.0.5"
Invoke-CheckedCommand -FilePath $venvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
Invoke-CheckedCommand -FilePath $venvPython -Arguments @("-m", "pip", "install", "-r", $requirements)
Invoke-CheckedCommand -FilePath $venvPython -Arguments @("-m", "pip", "install", "nuitka==4.0.5")

Write-Host "[3/6] Compiling with Nuitka"
Push-Location $ProjectRoot
try {
    Invoke-CheckedCommand -FilePath $venvPython -Arguments @("-m", "nuitka", "run_system_tray.py")
} finally {
    Pop-Location
}
Assert-PathExists -Path $distDir -Label "Nuitka dist output"

Write-Host "[4/6] Copying person detector intel folder"
$intelDest = Join-Path $distDir "src\video_recogniser\person_recogniser\intel"
if (Test-Path -LiteralPath $intelDest) {
    Remove-Item -LiteralPath $intelDest -Recurse -Force
}
New-Item -ItemType Directory -Path (Split-Path -Path $intelDest -Parent) -Force | Out-Null
Copy-Item -LiteralPath $intelSource -Destination $intelDest -Recurse -Force

Write-Host "[5/6] Copying OpenVINO libs into dist/openvino/libs"
$openvinoLibsSource = Join-Path $venvDir "Lib\site-packages\openvino\libs"
Assert-PathExists -Path $openvinoLibsSource -Label "OpenVINO libs in venv"
$openvinoLibsDest = Join-Path $distDir "openvino\libs"
New-Item -ItemType Directory -Path $openvinoLibsDest -Force | Out-Null
Copy-Item -Path (Join-Path $openvinoLibsSource "*") -Destination $openvinoLibsDest -Recurse -Force

Write-Host "[6/6] Copying OpenVINO DLLs into dist root"
$dllNames = @("openvino_intel_cpu_plugin.dll", "openvino_ir_frontend.dll")
foreach ($dllName in $dllNames) {
    $dllSource = Join-Path $openvinoLibsSource $dllName
    Assert-PathExists -Path $dllSource -Label "Required DLL"
    Copy-Item -LiteralPath $dllSource -Destination (Join-Path $distDir $dllName) -Force
}

Write-Host "Build automation complete. Output folder: $distDir"
