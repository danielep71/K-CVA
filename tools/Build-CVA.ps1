$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$build = Join-Path $root 'build'
$null = New-Item -ItemType Directory -Path $build -Force
$output = Join-Path $build 'K-CVA_Prototype.xlsm'
if (Test-Path $output) { throw 'K-CVA_Prototype.xlsm already exists. Move or rename it before building; it will not be overwritten.' }
$excel = $null
$book = $null
$created = $false
$success = $false
try {
    $excel = New-Object -ComObject Excel.Application
    $book = $excel.Workbooks.Open((Join-Path $root 'src\workbook\CVA_Template.xlsx'))
    try { $project = $book.VBProject; $null = $project.VBComponents.Count }
    catch { throw 'Excel blocks VBA project import. Enable Trust access to the VBA project object model in Excel Trust Center, then retry. No security settings were changed by this script.' }
    $sources = @(Get-ChildItem (Join-Path $root 'src') -Filter '*.bas' -Recurse)
    $sources += Get-Item (Join-Path $root 'tests\modules\TEST_Prototype.bas')
    foreach ($file in $sources) { $null = $project.VBComponents.Import($file.FullName) }
    $lines = Get-Content (Join-Path $root 'src\workbook\ThisWorkbook.cls')
    $start = [Array]::IndexOf($lines, 'Option Explicit')
    if ($start -lt 0) { throw 'ThisWorkbook source is malformed.' }
    $project.VBComponents.Item($book.CodeName).CodeModule.AddFromString(($lines[$start..($lines.Count - 1)] -join "`r`n"))
    $book.SaveAs($output, 52)
    $created = $true
    $macroPrefix = "'" + $book.Name.Replace("'", "''") + "'!"
    $excel.Run($macroPrefix + 'M_Main.InstallButtons')
    $excel.Run($macroPrefix + 'TEST_Prototype.RunPrototypeTests')
    $testSheet = $book.Worksheets.Item('TestCatalogue')
    for ($row = 7; $row -le 28; $row++) {
        if ($testSheet.Cells.Item($row, 7).Value2 -ne 'PASS') { throw "VBA regression case at row $row failed; inspect source and rebuild." }
    }
    $status = $excel.Run($macroPrefix + 'M_Main.RunCVA_Silent')
    if ($status -ne 'OK') { throw "Demo run failed: $status" }
    $actual = [double]$book.Worksheets.Item('Results').Range('E10').Value2
    if ([math]::Abs($actual - 553046.9653865349) -gt 0.000001) { throw "Demo mismatch: $actual" }
    $book.Save()
    $report = @("Built at: $(Get-Date -Format o)", "Excel version: $($excel.Version), build: $($excel.Build)", 'VBA runtime regression cases: 22/22 PASS', "Demo BA-CVA: $actual", 'Manual Excel UI/event checks: still required (see docs/prototype/VALIDATION.md)')
    $report | Set-Content (Join-Path $build 'Excel-build-evidence.txt')
    $success = $true
    Write-Host "Created $output; 22 VBA cases and the demo passed."
} finally {
    if ($null -ne $book) { $book.Close($false) }
    if ($null -ne $excel) { $excel.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) }
    if ($created -and -not $success -and (Test-Path $output)) { Remove-Item $output }
}
