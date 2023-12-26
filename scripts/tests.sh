set -e

DIR=$(dirname "$0")
cd "${DIR}/.."

# Optional parameter for selecting a specific test
selected_test=$1

if [ -n "$selected_test" ]; then
    # Run the selected test
    env ENVIRONMENT=TESTING python -m pytest "$selected_test" --cov=app --cov-report=term-missing -v
else
    # Run all tests
    env ENVIRONMENT=TESTING python -m pytest tests/ --cov=app --cov-report=term-missing -v
fi

coverage=$(env ENVIRONMENT=TESTING python -m pytest tests/ --cov=app --cov-report=term-missing -v | awk '/TOTAL/ {print $NF}' | tr -d '%')

if [ "$(awk 'BEGIN {print ("'$coverage'" < "'$coverage_threshold'") }')" -eq 1 ]; then
    echo "Coverage is below $coverage_threshold%. Aborting."
    exit 1
fi