param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SpecPath = Join-Path $ProjectRoot "PocketMedic.spec"

Push-Location $ProjectRoot
try {
    $args = @($SpecPath)
    if ($Clean) {
        $args = @("--clean") + $args
    }
    python -m PyInstaller @args
}
finally {
    Pop-Location
}
