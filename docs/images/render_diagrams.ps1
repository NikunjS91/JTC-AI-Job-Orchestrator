# Render Mermaid diagrams to SVG and PNG using either npx or Docker
# Usage (PowerShell):
#   Set-Location "$PSScriptRoot"
#   .\render_diagrams.ps1

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

$files = @(
  @{ in = 'current-architecture.mmd'; outSvg = 'current-architecture.svg'; outPng = 'current-architecture.png' },
  @{ in = 'proposed-architecture.mmd'; outSvg = 'proposed-architecture.svg'; outPng = 'proposed-architecture.png' }
)

function Render-With-Npx {
  param($f)
  Write-Host "Rendering $($f.in) with npx mermaid-cli..." -ForegroundColor Cyan
  npx --yes @mermaid-js/mermaid-cli -i $f.in -o $f.outSvg
  npx --yes @mermaid-js/mermaid-cli -i $f.in -o $f.outPng
}

function Render-With-Docker {
  param($f)
  Write-Host "Rendering $($f.in) with Docker mermaid-cli..." -ForegroundColor Cyan
  $mount = (Get-Location).Path
  docker run --rm -v "$mount:/data" ghcr.io/mermaid-js/mermaid-cli/mermaid-cli:latest -i "/data/$($f.in)" -o "/data/$($f.outSvg)"
  docker run --rm -v "$mount:/data" ghcr.io/mermaid-js/mermaid-cli/mermaid-cli:latest -i "/data/$($f.in)" -o "/data/$($f.outPng)"
}

$haveNode = Get-Command node -ErrorAction SilentlyContinue
$haveDocker = Get-Command docker -ErrorAction SilentlyContinue

foreach ($f in $files) {
  if ($haveNode) {
    try { Render-With-Npx $f; continue } catch { Write-Warning $_.Exception.Message }
  }
  if ($haveDocker) {
    try { Render-With-Docker $f; continue } catch { Write-Warning $_.Exception.Message }
  }
  Write-Warning "Could not render $($f.in). Install Node.js or Docker, or render online at https://mermaid.live using the .mmd file."
}

Write-Host "Done. Outputs (if successful) are .svg and .png files in this folder." -ForegroundColor Green
