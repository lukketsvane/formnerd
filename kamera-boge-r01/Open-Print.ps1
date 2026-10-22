param(
    [ValidateSet('Prove', 'Front', 'Rest', 'ProveGeometri', 'FrontGeometri', 'RestGeometri')]
    [string]$Plate = 'Prove',
    [switch]$VerifyOnly
)

$ErrorActionPreference = 'Stop'
$rootPath = [System.IO.Path]::GetFullPath($PSScriptRoot)
function Get-PackagePath {
    param([string]$RelativePath)
    $itemPath = [System.IO.Path]::GetFullPath((Join-Path $rootPath $RelativePath))
    if (-not $itemPath.StartsWith($rootPath + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Ugyldig filsti i manifestet.'
    }
    return $itemPath
}
$manifest = Get-Content -LiteralPath (Join-Path $rootPath 'package-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($entry in $manifest.files) {
    $itemPath = Get-PackagePath $entry.path
    if (-not (Test-Path -LiteralPath $itemPath -PathType Leaf)) {
        throw "Fila manglar: $($entry.path)"
    }
    $item = Get-Item -LiteralPath $itemPath
    $actual = (Get-FileHash -LiteralPath $itemPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($item.Length -ne $entry.bytes -or $actual -ne $entry.sha256) {
        throw "Filkontrollen feila: $($entry.path)"
    }
}
$largeFiles = Get-Content -LiteralPath (Join-Path $rootPath 'large-files.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($model in $largeFiles.files) {
    $destination = Get-PackagePath $model.path
    if (Test-Path -LiteralPath $destination) {
        if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) {
            throw "Målet er ikkje ei fil: $($model.path)"
        }
        $actual = (Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
        if ((Get-Item -LiteralPath $destination).Length -ne $model.bytes -or $actual -ne $model.sha256) {
            throw "Eksisterande fil er endra og blir ikkje overskriven: $($model.path)"
        }
        continue
    }
    $parentPath = Split-Path -Parent $destination
    New-Item -ItemType Directory -Path $parentPath -Force | Out-Null
    $temporary = $destination + '.partial-' + [guid]::NewGuid().ToString('N')
    try {
        $outputStream = [System.IO.File]::Open($temporary, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        try {
            foreach ($part in $model.parts) {
                $partPath = Get-PackagePath $part.path
                $inputStream = [System.IO.File]::OpenRead($partPath)
                try { $inputStream.CopyTo($outputStream) }
                finally { $inputStream.Dispose() }
            }
        } finally {
            $outputStream.Dispose()
        }
        $actual = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant()
        if ((Get-Item -LiteralPath $temporary).Length -ne $model.bytes -or $actual -ne $model.sha256) {
            throw "Samansetjinga feila: $($model.path)"
        }
        [System.IO.File]::Move($temporary, $destination)
    } finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}
Write-Host 'Filkontroll og tapsfri samansetjing godkjende.'
if ($VerifyOnly) { return }
$choices = @{
    Prove = 'print\bambu\Plate-00-prove-P1S.gcode.3mf'
    Front = 'print\bambu\Plate-01-framhus-P1S.gcode.3mf'
    Rest = 'print\bambu\Plate-02-deksel-og-smadelar-P1S.gcode.3mf'
    ProveGeometri = 'print\Plate-00-prove.3mf'
    FrontGeometri = 'print\Plate-01-framhus.3mf'
    RestGeometri = 'print\Plate-02-deksel-og-smadelar.3mf'
}
$target = Join-Path $rootPath $choices[$Plate]
$candidates = @()
$found = Get-Command 'bambu-studio.exe' -ErrorAction SilentlyContinue
if ($found) { $candidates += $found.Source }
foreach ($basePath in @($env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:LOCALAPPDATA)) {
    if ($basePath) {
        $candidates += Join-Path $basePath 'Bambu Studio\bambu-studio.exe'
        $candidates += Join-Path $basePath 'BambuStudio\bambu-studio.exe'
        $candidates += Join-Path $basePath 'Programs\Bambu Studio\bambu-studio.exe'
    }
}
$studio = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
Write-Host 'Dei slica filene er laga for P1S, 0,4 mm dyse, Textured PEI og Bambu PLA Basic. Kontroller plate og filament.'
Write-Host 'Dette opnar berre modellen. Inga utskrift blir starta.'
if ($studio) {
    Start-Process -FilePath $studio -ArgumentList ('"' + $target + '"')
} else {
    Write-Host 'Bambu Studio vart ikkje funne. Opnar filtilknytinga; kontroller at fila kjem opp i sliceren.'
    Start-Process -FilePath $target
}
