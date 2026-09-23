param([switch]$DryRun)
. "$PSScriptRoot/bootstrap.ps1" -ReadOnly
$arguments = @("$PSScriptRoot/stack.py", 'uninstall')
if ($DryRun) { $arguments += '--dry-run' }
& $env:SJOERD_PYTHON @arguments
exit $LASTEXITCODE
