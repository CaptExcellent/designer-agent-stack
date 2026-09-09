param([ValidateSet('auto','codex','claude-code')][string]$Agent='auto', [switch]$All, [switch]$Update, [switch]$DryRun, [switch]$SkipDependencies, [switch]$SerenaHooks, [switch]$NoSerenaHooks, [switch]$WithVercel, [switch]$NoVercel)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/bootstrap.ps1" -ReadOnly:$DryRun
$arguments = @("$PSScriptRoot/stack.py", 'install', '--agent', $Agent)
if ($All) { $arguments += '--all' }
if ($Update) { $arguments += '--update' }
if ($DryRun) { $arguments += '--dry-run' }
if ($SkipDependencies) { $arguments += '--skip-dependencies' }
if ($SerenaHooks -and $NoSerenaHooks) { throw 'Choose SerenaHooks or NoSerenaHooks.' }
if ($WithVercel -and $NoVercel) { throw 'Choose WithVercel or NoVercel.' }
if ($SerenaHooks) { $arguments += '--serena-hooks' }
if ($NoSerenaHooks) { $arguments += '--no-serena-hooks' }
if ($WithVercel) { $arguments += '--with-vercel' }
if ($NoVercel) { $arguments += '--no-with-vercel' }
& $env:SJOERD_PYTHON @arguments
exit $LASTEXITCODE
