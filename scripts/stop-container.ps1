param(
  [string]$Name = "petra-gpt-local"
)

Write-Host "Stopping container $Name..."
docker rm -f $Name -v | Out-Null
Write-Host "$Name stopped/removed (if it existed)."
