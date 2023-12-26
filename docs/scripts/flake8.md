# flake8.sh

### Description
Runs flake8 linter on `/app` directory and `/tests` directory.

### Running the command
To run the command you have to open your terminal on the main directory and run:

`sh scripts/flake8.sh`

### Examples

Example of a run whithout linter errors:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/flake8.sh
Running flake8
0
```

Example of a run with linter errors:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/flake8.sh
Running flake8
app/router.py:13:101: E501 line too long (104 > 100 characters)
    users.router, prefix="/userszdasdasdadasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasdasd")
                                                                                                    ^
1     E501 line too long (104 > 100 characters)
1
```