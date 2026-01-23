#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Archive legacy code directories after unified package migration.

.DESCRIPTION
    Moves src/agent-container and src/agent-foundry to archive/legacy-* directories.
    These directories are preserved for reference but no longer needed for deployment.

.PARAMETER DryRun
    Show what would be moved without actually moving files.

.EXAMPLE
    ./archive-legacy.ps1
    ./archive-legacy.ps1 -DryRun
#>

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$archiveDir = Join-Path $projectRoot "archive"
$timestamp = Get-Date -Format "yyyyMMdd"

Write-Host "🗂️  Archiving Legacy Code" -ForegroundColor Cyan
Write-Host "   Project root: $projectRoot" -ForegroundColor Gray
Write-Host ""

# Create archive directory
if (-not (Test-Path $archiveDir)) {
    if ($DryRun) {
        Write-Host "   Would create: $archiveDir" -ForegroundColor Yellow
    } else {
        New-Item -ItemType Directory -Path $archiveDir | Out-Null
        Write-Host "   ✓ Created archive directory" -ForegroundColor Green
    }
}

# Directories to archive
$legacyDirs = @(
    @{ Source = "src/agent-container"; Target = "archive/legacy-agent-container-$timestamp" },
    @{ Source = "src/agent-foundry"; Target = "archive/legacy-agent-foundry-$timestamp" },
    @{ Source = "src/shared"; Target = "archive/legacy-shared-$timestamp" }
)

foreach ($dir in $legacyDirs) {
    $sourcePath = Join-Path $projectRoot $dir.Source
    $targetPath = Join-Path $projectRoot $dir.Target

    if (Test-Path $sourcePath) {
        if ($DryRun) {
            Write-Host "   Would move: $($dir.Source) -> $($dir.Target)" -ForegroundColor Yellow
        } else {
            Move-Item -Path $sourcePath -Destination $targetPath
            Write-Host "   ✓ Moved: $($dir.Source) -> $($dir.Target)" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠ Not found (already archived?): $($dir.Source)" -ForegroundColor DarkYellow
    }
}

# Create a README in the archive directory
$archiveReadme = @"
# Archived Legacy Code

These directories contain the original code structure before the unified agent package migration.

**Archived on:** $(Get-Date -Format "yyyy-MM-dd")

## Directories

- `legacy-agent-container-*`: Original Container Apps specific code
- `legacy-agent-foundry-*`: Original Foundry native agent code
- `legacy-shared-*`: Original shared business logic

## Current Location

All functionality has been migrated to the unified package:

- `src/agent/` - Unified agent package (works for both deployment targets)

## Migration Guide

See [docs/refactoring/](../docs/refactoring/) for the migration planning documents.

## Restoration

If needed, you can restore these by moving them back:

```powershell
Move-Item archive/legacy-agent-container-* src/agent-container
Move-Item archive/legacy-agent-foundry-* src/agent-foundry
Move-Item archive/legacy-shared-* src/shared
```
"@

$archiveReadmePath = Join-Path $archiveDir "README.md"

if ($DryRun) {
    Write-Host ""
    Write-Host "   Would create: archive/README.md" -ForegroundColor Yellow
} else {
    $archiveReadme | Out-File -FilePath $archiveReadmePath -Encoding utf8
    Write-Host ""
    Write-Host "   ✓ Created archive/README.md" -ForegroundColor Green
}

Write-Host ""
if ($DryRun) {
    Write-Host "   [DRY RUN] No files were moved" -ForegroundColor Cyan
} else {
    Write-Host "   ✅ Legacy code archived successfully" -ForegroundColor Green
    Write-Host ""
    Write-Host "   The unified package is now at: src/agent/" -ForegroundColor White
}
