# Helper para gestionar worktrees por agente (Windows PowerShell).
# Uso:
#   .\scripts\new-worktree.ps1 -Name researcher -Branch feat/researcher-places-cache
#   .\scripts\new-worktree.ps1 -Name researcher -Remove

param(
  [Parameter(Mandatory = $true)][string]$Name,
  [string]$Branch = "",
  [switch]$Remove
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$WtPath = Join-Path (Split-Path -Parent $RepoRoot) ("factoryMark-wt-" + $Name)

if ($Remove) {
  git -C $RepoRoot worktree remove --force $WtPath
  git -C $RepoRoot worktree prune
  Write-Output "Removed $WtPath"
  exit 0
}

if ([string]::IsNullOrWhiteSpace($Branch)) { throw "Pasá -Branch feat/... para crear." }
git -C $RepoRoot worktree add $WtPath -b $Branch
Write-Output "Created $WtPath on $Branch"
Write-Output "Recordá: cada worktree necesita su propio 'uv sync' y/o 'pnpm install', y puertos distintos."
