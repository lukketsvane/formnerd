$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$check = & tripo.cmd doctor 2>&1
if ($LASTEXITCODE -ne 0) { throw 'Tripo CLI needs browser authorization: tripo login --region ov' }
$source = '.\reference\tripo_reference_square.jpg'
& tripo.cmd make $source --model tripo-v3.1 -p texture=false -p pbr=false -p geometry_quality=detailed -p auto_size=false -p enable_image_autofix=false -p export_uv=false --seed 20261023 --out '.\tripo\master' --name ENTROPI_STEREO_R08_MASTER --json --no-open --yes
if ($LASTEXITCODE -ne 0) { throw 'Tripo generation did not finish successfully. Inspect task history before retrying.' }
& tripo.cmd mesh decimate '@last' --model v3.0 --face-limit 20000 --no-bake --out '.\tripo\lowpoly' --name ENTROPI_STEREO_R08_LOW_POLY --json --no-open --yes
if ($LASTEXITCODE -ne 0) { throw 'Tripo master is preserved. Decimation failed and can be retried without regenerating master.' }
