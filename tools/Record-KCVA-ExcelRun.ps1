<#
.SYNOPSIS
    Records an Excel run of the checked-out commit in one command, and checks it.

.DESCRIPTION
    Automates INSTALLATION.md, Recording an Excel run, on a Windows host with
    desktop Excel, Git and Python 3.12 or later:

    1. Takes the checked-out commit as the candidate; refuses a checkout with
       local changes to tracked files.
    2. Makes the evidence folder test-results\excel-run-<sha7>\ (ignored by
       Git), with exported\ inside.
    3. Starts Excel through COM, adds a blank workbook and saves it as
       test-results\K-CVA-excel-run-<sha7>.xlsm.
    4. Imports every VBA component the commit tracks: src\core, src\classes,
       src\modules, src\workbook, then tests\modules, each sorted by name.
       It stops if the commit holds forms or document modules, which this
       script does not import yet.
    5. Compiles with the VBA editor's own Debug > Compile VBAProject and
       records PASS when Excel then disables the command, as it does after a
       compile without error. A compile error appears in a message box: read
       it, click OK, and the run goes on with the compile recorded as FAIL.
    6. Runs TEST_Examples.SaveExampleEvidence on the folder: the three logs.
    7. Exports every component back into exported\.
    8. Writes host.txt: the Windows version, the project's references, the
       compile result, the Excel build and the VBA project access.
    9. Closes Excel and runs tools\check_excel_run.py on the folder, saving
       its report as check.txt. The exit code is the checker's.

    Importing, compiling and exporting through COM needs "Trust access to the
    VBA project object model". If it is off, the script turns it on for the
    current user only, for this run, and restores the previous value when the
    run ends; host.txt records the restoration path taken, not an independent
    read-back. Before changing the setting, it stops if the current-user
    policy disables access or Excel is already running. An explicitly
    enabled current-user policy is accepted and is not overridden.
    The macro security level is never changed.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File tools\Record-KCVA-ExcelRun.ps1

    Or double-click tools\Record-KCVA-ExcelRun.cmd.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$userSecurity = 'HKCU:\Software\Microsoft\Office\16.0\Excel\Security'
$policySecurity = 'HKCU:\Software\Policies\Microsoft\Office\16.0\Excel\Security'
# Import order of INSTALLATION.md, Importing VBA into Excel
$sourceRoots = @('src/core', 'src/classes', 'src/modules', 'src/workbook', 'tests/modules')
$vbaSuffixes = @('.bas', '.cls', '.frm')
# 1 = standard module, 2 = class module, 3 = form; 100 = document module
$exportableTypes = @(1, 2, 3)
$exportSuffix = @{ 1 = '.bas'; 2 = '.cls'; 3 = '.frm' }

function Get-RegistryValue {
    param([string]$Path, [string]$Name)
    $item = Get-ItemProperty -Path $Path -Name $Name -ErrorAction SilentlyContinue
    if ($null -eq $item) { return $null }
    return $item.$Name
}

function Release-Com {
    param($Object)
    if ($null -ne $Object) {
        [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($Object)
    }
}

# The VBA editor's objects give Windows PowerShell no type information, so
# these helpers reach them through IDispatch by name. The leading comma keeps
# a returned collection as one object instead of unrolling it.
function Get-ComProperty {
    param($Object, [string]$Name, [object[]]$Arguments = @())
    return ,([System.__ComObject].InvokeMember($Name, [System.Reflection.BindingFlags]::GetProperty,
                                               $null, $Object, $Arguments))
}

function Set-ComProperty {
    param($Object, [string]$Name, $Value)
    [void][System.__ComObject].InvokeMember($Name, [System.Reflection.BindingFlags]::SetProperty,
                                            $null, $Object, @($Value))
}

function Invoke-ComMethod {
    param($Object, [string]$Name, [object[]]$Arguments = @())
    return ,([System.__ComObject].InvokeMember($Name, [System.Reflection.BindingFlags]::InvokeMethod,
                                               $null, $Object, $Arguments))
}

function Get-WindowsName {
    # The same facts winver shows: edition, version and OS build
    $key = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    $product = Get-RegistryValue $key 'ProductName'
    $display = Get-RegistryValue $key 'DisplayVersion'
    $build = Get-RegistryValue $key 'CurrentBuild'
    $revision = Get-RegistryValue $key 'UBR'
    # Windows 11 keeps "Windows 10" in ProductName; the build tells them apart
    if ($build -and [int]$build -ge 22000 -and $product -like 'Windows 10*') {
        $product = $product -replace '^Windows 10', 'Windows 11'
    }
    return "$product, version $display, OS build $build.$revision"
}

function Get-Components {
    # The commit's tracked VBA components, in import order
    $listed = @(& git ls-files -- @sourceRoots)
    if ($LASTEXITCODE -ne 0) { throw 'git ls-files failed' }
    $found = @()
    foreach ($root in $sourceRoots) {
        $found += @($listed | Where-Object {
            ([System.IO.Path]::GetDirectoryName($_) -replace '\\', '/') -eq $root -and
            $vbaSuffixes -contains [System.IO.Path]::GetExtension($_).ToLowerInvariant()
        } | Sort-Object)
    }
    $outside = @(& git ls-files | Where-Object {
        $vbaSuffixes -contains [System.IO.Path]::GetExtension($_).ToLowerInvariant()
    } | Where-Object { $found -notcontains $_ })
    if ($outside.Count -gt 0) {
        throw "VBA components outside the import folders: $($outside -join ', ')"
    }
    foreach ($path in $found) {
        $extension = [System.IO.Path]::GetExtension($path).ToLowerInvariant()
        if ($extension -eq '.frm') {
            throw "$path is a form; this script does not import forms yet: use the manual procedure"
        }
        if ($extension -eq '.cls') {
            $head = Get-Content -Path $path -TotalCount 12
            if ($head -match '^Attribute VB_PredeclaredId = True' -and $head -match '^Attribute VB_Base') {
                throw "$path is a document module; this script does not import those yet: use the manual procedure"
            }
        }
    }
    return $found
}

# --- Preconditions ------------------------------------------------------------

foreach ($tool in 'git', 'python') {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        throw "$tool was not found on PATH"
    }
}
$status = @(& git status --porcelain --untracked-files=no)
if ($status.Count -gt 0) {
    throw "The checkout has local changes; commit, stash or discard them first:`n$($status -join "`n")"
}
$sha = (& git rev-parse HEAD).Trim()
$components = Get-Components
if ($components.Count -eq 0) { throw "Commit $sha holds no VBA component" }
if (Get-Process -Name EXCEL -ErrorAction SilentlyContinue) {
    throw 'Excel is running. Save your work, close every Excel window, then run again.'
}
$policyAccess = Get-RegistryValue $policySecurity 'AccessVBOM'
if ($null -ne $policyAccess -and [int]$policyAccess -ne 1) {
    throw 'A policy turns off "Trust access to the VBA project object model"; this script cannot run here. Use the manual procedure (INSTALLATION.md, Recording an Excel run).'
}

$short = $sha.Substring(0, 7)
$results = Join-Path $repoRoot 'test-results'
$bundle = Join-Path $results "excel-run-$short"
if (Test-Path $bundle) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    Rename-Item -Path $bundle -NewName ((Split-Path -Leaf $bundle) + "-before-$stamp")
}
$exported = Join-Path $bundle 'exported'
New-Item -ItemType Directory -Force -Path $exported | Out-Null
$workbookPath = Join-Path $results "K-CVA-excel-run-$short.xlsm"
if (Test-Path $workbookPath) { Remove-Item -Path $workbookPath -Force }

Write-Host "Candidate: $sha"
Write-Host "Evidence:  $bundle"

# --- VBA project access, for this run only -------------------------------------

$previousAccess = Get-RegistryValue $userSecurity 'AccessVBOM'
$accessChanged = $false
if ($null -eq $policyAccess -and ($null -eq $previousAccess -or [int]$previousAccess -ne 1)) {
    if (-not (Test-Path $userSecurity)) { New-Item -Path $userSecurity -Force | Out-Null }
    New-ItemProperty -Path $userSecurity -Name 'AccessVBOM' -Value 1 -PropertyType DWord -Force | Out-Null
    $accessChanged = $true
    Write-Host 'VBA project access: turned on for this run; it is restored at the end.'
}

$compile = 'NOT_RUN'
$references = ''
$excelBuild = ''
$failure = $null
$excel = $null
$workbook = $null
$project = $null
$vbComponents = $null
$referenceList = $null
$vbe = $null
$bars = $null
$control = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $true
    $excel.DisplayAlerts = $false
    $excelBuild = Get-RegistryValue 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' 'VersionToReport'
    if (-not $excelBuild) { $excelBuild = "$($excel.Version).$($excel.Build)" }

    $workbook = $excel.Workbooks.Add()
    # 52 = xlOpenXMLWorkbookMacroEnabled
    $workbook.SaveAs($workbookPath, 52)

    Write-Host '== Import'
    $project = $workbook.VBProject
    $vbComponents = $project.VBComponents
    foreach ($path in $components) {
        Write-Host "   $path"
        [void]$vbComponents.Import((Join-Path $repoRoot $path))
    }

    $referenceList = Get-ComProperty $project 'References'
    $count = [int](Get-ComProperty $referenceList 'Count')
    $references = (@(for ($index = 1; $index -le $count; $index++) {
        [string](Get-ComProperty (Invoke-ComMethod $referenceList 'Item' @($index)) 'Description')
    }) -join '; ')

    Write-Host '== Compile'
    $vbe = Get-ComProperty $excel 'VBE'
    try { Set-ComProperty (Get-ComProperty $vbe 'MainWindow') 'Visible' $true } catch { }
    # 578 is Debug > Compile VBAProject; 1 = msoControlButton
    $bars = Get-ComProperty $vbe 'CommandBars'
    $control = Invoke-ComMethod $bars 'FindControl' @(1, 578)
    if ($null -eq $control) {
        $compile = 'FAIL: Debug > Compile VBAProject not found in the VBA editor'
    } else {
        if ([bool](Get-ComProperty $control 'Enabled')) { [void](Invoke-ComMethod $control 'Execute') }
        if ([bool](Get-ComProperty $control 'Enabled')) {
            $compile = 'FAIL: Debug > Compile VBAProject reported a compile error'
        } else {
            $compile = 'PASS'
        }
    }
    try { Set-ComProperty (Get-ComProperty $vbe 'MainWindow') 'Visible' $false } catch { }
    Write-Host "   $compile"

    Write-Host '== Run'
    if ($compile -eq 'PASS') {
        # The logs record the outcome of each run; their errors are printed,
        # not raised. An error that still escapes is recorded, and the export
        # below runs anyway.
        try {
            [void]$excel.Run("'$($workbook.Name)'!TEST_Examples.SaveExampleEvidence", $bundle)
        } catch {
            $failure = "SaveExampleEvidence: $($_.Exception.Message)"
            Write-Host "   $failure"
        }
        foreach ($log in 'examples.log', 'injected.log', 'skipped.log') {
            $state = if (Test-Path (Join-Path $bundle $log)) { 'saved' } else { 'MISSING' }
            Write-Host "   $log $state"
        }
    } else {
        Write-Host '   not run: the project did not compile'
    }

    Write-Host '== Export'
    foreach ($component in $vbComponents) {
        $type = [int]$component.Type
        if ($exportableTypes -contains $type) {
            $component.Export((Join-Path $exported ($component.Name + $exportSuffix[$type])))
        }
    }
    $workbook.Save()
} catch {
    $failure = (@($failure, $_.Exception.Message) | Where-Object { $_ }) -join '; '
    Write-Host "STOPPED: $($_.Exception.Message)"
} finally {
    foreach ($object in $control, $bars, $vbe, $referenceList, $vbComponents, $project) { Release-Com $object }
    if ($null -ne $workbook) { try { $workbook.Close($false) } catch { }; Release-Com $workbook }
    if ($null -ne $excel) { try { $excel.Quit() } catch { }; Release-Com $excel }
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    if ($accessChanged) {
        if ($null -eq $previousAccess) {
            Remove-ItemProperty -Path $userSecurity -Name 'AccessVBOM' -ErrorAction SilentlyContinue
        } else {
            Set-ItemProperty -Path $userSecurity -Name 'AccessVBOM' -Value $previousAccess
        }
        Write-Host 'VBA project access: restored.'
    }
}

if ($accessChanged) {
    $access = 'turned on for this run by tools/Record-KCVA-ExcelRun.ps1, then restored'
} elseif ($null -ne $policyAccess) {
    $access = 'on, set by policy'
} else {
    $access = 'already on'
}
# $host is a PowerShell automatic variable: the record is $hostRecord
$hostRecord = @(
    "windows=$(Get-WindowsName)",
    "references=$references",
    "compile=$compile",
    "excel_build=$excelBuild",
    "vba_project_access=$access",
    "recorded_by=tools/Record-KCVA-ExcelRun.ps1"
)
if ($failure) { $hostRecord += "stopped=$failure" }
$hostRecord | Out-File -FilePath (Join-Path $bundle 'host.txt') -Encoding ascii

Write-Host '== Check'
# Windows PowerShell turns a native command's redirected stderr into error
# records, which 'Stop' would make fatal: the checker's exit code decides.
$ErrorActionPreference = 'Continue'
$report = Join-Path $bundle 'check.txt'
$output = @(& python tools\check_excel_run.py $bundle --commit $sha 2>&1 | ForEach-Object { [string]$_ })
$result = $LASTEXITCODE
$output | Out-File -FilePath $report -Encoding utf8
$output | ForEach-Object { Write-Host $_ }
Write-Host ''
Write-Host "Report: $report"
exit $result
