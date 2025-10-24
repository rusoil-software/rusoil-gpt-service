<#
.SYNOPSIS
  Build the Docker image and run it locally (PowerShell)

.NOTES
  Usage: ./scripts/build-and-run.ps1 -Tag usptu-local
#>
param(
  [string]$Tag = "rusoil-gpt-service:local",
  [int]$Port = 8000
)

Write-Host "Building image $Tag..."
docker build -t $Tag .

Write-Host "Running container $Tag on port $Port..."
docker run -d --name usptu-local -p ${Port}:8000 $Tag | Out-Null
Write-Host "Container started. Use 'docker logs -f usptu-local' to follow logs." 
