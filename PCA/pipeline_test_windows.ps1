# Runs all test files - Windows version

# Remove virtual environment if it exists
if (Test-Path .venv) {
    Remove-Item -Recurse -Force .venv
}

# Create new virtual environment
python -m venv .venv

# Remove previous results
if (Test-Path "$env:USERPROFILE\Documents\PCA_Analysis\results") {
    Remove-Item -Recurse -Force "$env:USERPROFILE\Documents\PCA_Analysis\results"
}

# Activate virtual environment and install requirements
& .\.venv\Scripts\Activate.ps1
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
}

$test_files = "test_data"

# Process each test file
Get-ChildItem -Path $test_files -File | ForEach-Object {
    python "pca_pipeline.py" $_.FullName
}

# Count test files and pdfs
$num_tests = (Get-ChildItem -Path $test_files -File).Count
$num_pdfs = (Get-ChildItem -Path "$env:USERPROFILE\Documents\PCA_Analysis\results" -Filter "*.pdf").Count

# Compare counts and output results
if ($num_tests -eq $num_pdfs) {
    Write-Host "Test files and PDF outputs match ($num_tests)."
} else {
    Write-Host "Mismatch: $num_tests test files, $num_pdfs PDF files."
}