<#
.SYNOPSIS
  Build the Docker image and run it locally (PowerShell)

.NOTES
  Usage: ./scripts/build-and-run.ps1 -Tag petra-gpt-local
#>
param(
  [string]$Tag = "petra-gpt-service:local",
  [int]$Port = 8000
)

Write-Host "Building image $Tag..."
docker build -t $Tag .

Write-Host "Running container $Tag on port $Port..."
docker run -d --name petra-gpt-local -p ${Port}:8000 $Tag | Out-Null
Write-Host "Container started. Use 'docker logs -f petra-gpt-local' to follow logs." 
