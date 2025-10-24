<#
.SYNOPSIS
  Start the lightweight smoke server for local development.

.NOTES
  Run in PowerShell (Windows). Ensure Python is on PATH.
#>
param(
  [int]$Port = 8000
)

Write-Host "Starting smoke server on http://0.0.0.0:$Port"
python.exe "$(Resolve-Path -Relative "backend/smoke_server.py")"  
