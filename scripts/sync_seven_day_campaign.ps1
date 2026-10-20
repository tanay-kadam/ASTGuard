param([switch]$IncludePredictions)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$destination = Join-Path $taskRoot 'artifacts\seven_day_20261012'
New-Item -ItemType Directory -Force $destination | Out-Null
$sshBin = 'C:\Windows\System32\OpenSSH\ssh.exe'
$scpBin = 'C:\Windows\System32\OpenSSH\scp.exe'
$remoteRoot = '/tmp/astguard_seven_day_20261012/artifacts/seven_day_20261012'
# Exact named reports only: do not mirror private raw records or checkpoints.
$reports = @('plan.json','launch.json','authorization.json','source_files.json',
    'synthetic_integrity.json','campaign_status.json','verified_metrics.json',
    'resource_wait_status.json','resource_contention.jsonl','external_analysis.json',
    'external_analysis_failure.json','deadline_status.json','selection_diagnostic.json','synthetic_control_checks.json',
    'source_additions_check.json','dataset_provenance.json','added_pipeline_tests.log','prelaunch_tests.log',
    'prelaunch_tests_attempt2.log','holdout/component_report.json',
    'holdout/collision_report.json','holdout/manifest.json','holdout/extraction_retry.json',
    'holdout/extraction_retry1.json','holdout/extraction_retry2.json',
    'holdout/failure.json','holdout/failure_attempt1.json','holdout/failure_attempt2.json',
    'holdout/features_retry2.log','holdout/feature_integrity_check.json','progress_check.json',
    'user_decisions_20261012.json','deadline_amendment_20261012.json',
    'deadline_guard_status.json','deadline_guard.log')
foreach ($relative in $reports) {
    & $sshBin -o BatchMode=yes seeklab "test -f $remoteRoot/$relative"
    if ($LASTEXITCODE -ne 0) { continue }
    $target = Join-Path $destination $relative
    New-Item -ItemType Directory -Force (Split-Path -Parent $target) | Out-Null
    & $scpBin -o BatchMode=yes "seeklab:$remoteRoot/$relative" $target
    if ($LASTEXITCODE -ne 0) { throw "Failed to pull $relative" }
}
if ($IncludePredictions) {
    & $scpBin -o BatchMode=yes -r "seeklab:$remoteRoot/external_evaluation" $destination
    if ($LASTEXITCODE -ne 0) { throw 'Failed to pull external predictions' }
}
if (Test-Path (Join-Path $destination 'campaign_status.json')) {
    Get-Content (Join-Path $destination 'campaign_status.json')
}
