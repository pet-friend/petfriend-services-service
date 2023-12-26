# pylint.sh

### Description

Runs mypy linter on `/app` directory and `/tests` directory.

### Running the command

To run the command you have to open your terminal on the main directory and run:

`sh scripts/mypy.sh`

### Examples

Example of a run whithout linter errors:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/mypy.sh
Running mypy
Success: no issues found in 13 source files
```

Example of a run with linter errors:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/mypy.sh
Running mypy
app/main.py:19: error: Incompatible types in assignment (expression has type "str", variable has type "int")  [assignment]
Found 1 error in 1 file (checked 1 source file)
```
