@echo off
REM Mock ONE Simulator for Testing
REM This script simulates the ONE simulator for integration tests

echo [MOCK] ONE Simulator Starting...
echo [MOCK] Arguments: %*

REM Parse arguments
set BATCH_COUNT=0
set SETTINGS_FILE=

:parse_args
if "%~1"=="" goto done_parsing
if "%~1"=="-b" (
    set BATCH_COUNT=%~2
    shift
    shift
    goto parse_args
)
set SETTINGS_FILE=%~1
shift
goto parse_args

:done_parsing

echo [MOCK] Batch Count: %BATCH_COUNT%
echo [MOCK] Settings File: %SETTINGS_FILE%

REM Create mock report output directory
if not exist "reportQP" mkdir reportQP

REM Create dummy report files
echo sim_time: 43200 > reportQP\mock_report_MessageStatsReport.txt
echo created: 100 >> reportQP\mock_report_MessageStatsReport.txt
echo delivered: 45 >> reportQP\mock_report_MessageStatsReport.txt
echo delivery_prob: 0.45 >> reportQP\mock_report_MessageStatsReport.txt

echo [MOCK] ONE Simulator Completed Successfully
exit /b 0
