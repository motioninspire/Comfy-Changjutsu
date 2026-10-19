# Usage: .\install.ps1 -Comfy C:\ComfyUI [-WithBernini] [-SkipModels]
param(
  [Parameter(Mandatory=$true)][string]$Comfy,
  [switch]$WithBernini,
  [switch]$SkipModels
)
$py = $null
foreach ($c in @("$Comfy\venv\Scripts\python.exe", "$Comfy\.venv\Scripts\python.exe", "$Comfy\..\python_embeded\python.exe")) {
  if (-not $py -and (Test-Path $c)) { $py = $c }
}
if (-not $py) { $py = "python" }
Write-Host "Using python: $py"
$args = @("--comfy", $Comfy)
if ($WithBernini) { $args += "--with-bernini" }
if ($SkipModels)  { $args += "--skip-models" }
& $py "$PSScriptRoot\install.py" @args
