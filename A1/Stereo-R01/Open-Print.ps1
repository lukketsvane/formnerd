param([ValidateSet('Prove','Front','Bak')][string]$Plate = 'Prove')
$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
python (Join-Path $project 'source\restore_payloads.py')
if ($LASTEXITCODE -ne 0) { throw 'Kunne ikkje setje saman payload-filene.' }
$names = @{ Prove='Plate-00-prove'; Front='Plate-01-front'; Bak='Plate-02-bak-og-berar' }
$file = Join-Path $project ('print\bambu\' + $names[$Plate] + '.gcode.3mf')
if (-not (Test-Path -LiteralPath $file)) { $file = Join-Path $project ('print\plates\' + $names[$Plate] + '.3mf') }
if (-not (Test-Path -LiteralPath $file)) { throw ('Mangler platefil: ' + $file) }
$app = 'C:\Program Files\Bambu Studio\bambu-studio.exe'
if (-not (Test-Path -LiteralPath $app)) { throw 'Finn ikkje Bambu Studio i standardmappa.' }
Start-Process -FilePath $app -ArgumentList ('"' + $file + '"')
Write-Host ('Opna: ' + $file)
Write-Host 'Kontroller plate, materiale og filamenttilordning i Bambu Studio for utskrift.'
