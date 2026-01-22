#!/bin/bash
# Mock ONE Simulator for Testing
# This script simulates the ONE simulator for integration tests

echo "[MOCK] ONE Simulator Starting..."
echo "[MOCK] Arguments: $@"

# Parse arguments
BATCH_COUNT=0
SETTINGS_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -b)
            BATCH_COUNT="$2"
            shift 2
            ;;
        *)
            SETTINGS_FILE="$1"
            shift
            ;;
    esac
done

echo "[MOCK] Batch Count: $BATCH_COUNT"
echo "[MOCK] Settings File: $SETTINGS_FILE"

# Create mock report output directory
mkdir -p reportQP

# Create dummy report files
cat > reportQP/mock_report_MessageStatsReport.txt << EOF
sim_time: 43200
created: 100
delivered: 45
delivery_prob: 0.45
EOF

echo "[MOCK] ONE Simulator Completed Successfully"
exit 0
