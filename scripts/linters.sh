current_dir=$(dirname "$0")

# Function to execute a script and check its exit status
run_script() {
    script_name="$1"
    "${current_dir}/${script_name}"
    if [ $? -ne 0 ]; then
        echo "Error: ${script_name} failed. Aborting."
        exit 1
    fi
}

run_script "flake8.sh"
run_script "pylint.sh"
run_script "mypy.sh"