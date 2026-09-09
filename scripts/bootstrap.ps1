param([switch]$ReadOnly)
$ErrorActionPreference = 'Stop'
$uvCommand = Get-Command uv -ErrorAction SilentlyContinue
$uvPath = if ($uvCommand) { $uvCommand.Source } else { Join-Path $env:USERPROFILE '.local/bin/uv.exe' }
if (-not (Test-Path -LiteralPath $uvPath)) {
    if ($ReadOnly) { throw 'uv is missing. Run scripts/install.ps1 first.' }
    $download = Join-Path ([IO.Path]::GetTempPath()) ('sjoerd-uv-' + [guid]::NewGuid() + '.ps1')
    Invoke-WebRequest 'https://astral.sh/uv/install.ps1' -OutFile $download
    $oldNoPath = $env:UV_NO_MODIFY_PATH
    try { $env:UV_NO_MODIFY_PATH = '1'; & $download } finally { $env:UV_NO_MODIFY_PATH = $oldNoPath }
    if (-not (Test-Path -LiteralPath $uvPath)) { throw 'uv installation failed.' }
}
$pythonPath = & $uvPath python find --no-python-downloads 3.13 2>$null
if ($LASTEXITCODE -ne 0 -and -not $ReadOnly) {
    & $uvPath python install 3.13
    if ($LASTEXITCODE -ne 0) { Write-Warning 'uv reported an install/link error; checking the actual interpreter before proceeding.' }
}
$pythonPath = & $uvPath python find --no-python-downloads 3.13
if ($LASTEXITCODE -ne 0) { throw 'Python 3.13 is missing. Run install first.' }
& $pythonPath -c 'import sys; assert sys.version_info[:2] == (3, 13)'
if ($LASTEXITCODE -ne 0) { throw 'Python interpreter validation failed.' }
$env:SJOERD_UV = $uvPath
$env:SJOERD_PYTHON = $pythonPath
