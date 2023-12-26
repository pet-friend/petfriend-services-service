# pylint.sh

### Description
Runs pylint linter on `/app` directory and `/tests` directory.

### Running the command
To run the command you have to open your terminal on the main directory and run:

`sh scripts/pylint.sh`

### Examples

Example of a run whithout linter errors:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/pylint.sh
Running pylint

-------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 9.93/10, +0.07)
```

Example of a run with linter errors:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/pylint.sh
Running pylint
************* Module app.repositories.users
app/repositories/users.py:3:0: C0411: third party import "from sqlalchemy.orm import Session" should be placed before "from app.models.users import User" (wrong-import-order)
************* Module app.routes.users
app/routes/users.py:7:0: C0411: third party import "from fastapi import APIRouter, Depends" should be placed before "from app.db import get_db" (wrong-import-order)
************* Module tests.tests_setup
tests/tests_setup.py:5:0: E0401: Unable to import 'app.database' (import-error)
tests/tests_setup.py:5:0: E0611: No name 'database' in module 'app' (no-name-in-module)

------------------------------------------------------------------
Your code has been rated at 9.20/10 (previous run: 9.20/10, +0.00)
```