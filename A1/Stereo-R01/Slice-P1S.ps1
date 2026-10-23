param([ValidateSet('Prove','Front','Bak','Alle')][string]$Plate = 'Prove')
$ErrorActionPreference = 'Stop'
$project = $PSScriptRoot
$app = 'C:\Program Files\Bambu Studio\bambu-studio.exe'
$profiles = 'C:\Program Files\Bambu Studio\resources\profiles\BBL'
python (Join-Path $project 'source\restore_payloads.py')
if ($LASTEXITCODE -ne 0) { throw 'Payload-kontrollen feila.' }
$output = Join-Path $project 'print\bambu'
$profileOutput = Join-Path $output 'profiles'
New-Item -ItemType Directory -Force -Path $output | Out-Null
python (Join-Path $project 'source\bambu_profiles.py') $profiles $profileOutput
if ($LASTEXITCODE -ne 0) { throw 'Profilbygging feila.' }
$names = @{ Prove='Plate-00-prove'; Front='Plate-01-front'; Bak='Plate-02-bak-og-berar' }
$selected = if ($Plate -eq 'Alle') { @('Prove','Front','Bak') } else { @($Plate) }
foreach ($which in $selected) {
    $name = $names[$which]
    $inputFile = Join-Path $project ('print\plates\' + $name + '.3mf')
    $outputFile = Join-Path $output ($name + '.gcode.3mf')
    $stdout = Join-Path $output ($name + '.stdout.log')
    $stderr = Join-Path $output ($name + '.stderr.log')
    $settings = (Join-Path $profileOutput 'machine.json') + ';' + (Join-Path $profileOutput 'process.json')
    $filament = Join-Path $profileOutput 'filament.json'
    $arguments = @('--debug','1','--orient','0','--arrange','0','--load-settings',('"' + $settings + '"'),'--load-filaments',('"' + $filament + '"'),'--slice','0','--export-3mf',('"' + $outputFile + '"'),('"' + $inputFile + '"'))
    $process = Start-Process -FilePath $app -ArgumentList $arguments -Wait -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $outputFile)) {
        Get-Content $stdout -Tail 35
        Get-Content $stderr -Tail 35
        throw ('Slicing feila for ' + $name + ', exit ' + $process.ExitCode)
    }
    python (Join-Path $project 'source\check_slice.py') $outputFile
    if ($LASTEXITCODE -ne 0) { throw ('Kontrollen feila for ' + $name) }
    Write-Host ('Slica og kontrollert: ' + $outputFile)
}
