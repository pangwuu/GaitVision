#!/bin/bash

# Runs all test files - Linux/Mac version

# UNCOMMENT THE BELOW LINE IF YOU HAVE ISSUES WITH DEPENDENCIES
# rm -rf .venv 
python3 -m venv .venv

# Test results will be created in a separate test_results directory. This will be wiped each time tests are run
rm -rf ~/Documents/PCA_Analysis/test_results

source .venv/bin/activate
[ -f "requirements.txt" ] && pip install -r requirements.txt

# Needed for coverage reports
pip install coverage

test_files="test_data"

# Run the pipeline for each file in the test directory in test mode
for test_file in "$test_files"/*; do
    if [[ -f "$test_file" ]]; then
        coverage run --append pca_pipeline.py "$(realpath "$test_file")" "--test" 
    fi
done

# Count test csv files and pdfs
num_tests=$(find "$test_files" -type f -name "*.csv" | wc -l)
num_pdfs=$(find ~/Documents/PCA_Analysis/test_results -maxdepth 1 -type f -name "*.pdf" | wc -l)

if [[ "$num_tests" -eq "$num_pdfs" ]]; then
    echo "Test files and PDF outputs match ($num_tests)."
else
    echo "Mismatch: $num_tests test files, $num_pdfs PDF files."
fi

# Generate coverage report
coverage report -m
coverage html
open htmlcov/index.html