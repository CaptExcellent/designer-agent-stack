param()
. "$PSScriptRoot/bootstrap.ps1" -ReadOnly
& $env:SJOERD_PYTHON "$PSScriptRoot/stack.py" doctor
exit $LASTEXITCODE
