# linters.sh

### Description

Runs [flake8.sh](flake8.md), [pylint.sh](pylint.md) scripts and [mypy.md](mypy.md) scripts.

### Running the command

To run the command you have to open your terminal on the main directory and run:

`sh scripts/linters.sh`

### Examples

Example of a run whithout linter errors:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/linters.sh

Running flake8
0
Running pylint

------------------------------------
Your code has been rated at 10.00/10
Running mypy
Success: no issues found in 13 source files
```

Example of a run with linter errors:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/linters.sh

Running flake8
app/router.py:13:101: E501 line too long (144 > 100 characters)
    users.router, prefix="/usersasdadasdghasdhkjashflkashjf,ashlkajs.kfja,sfhkajshfmasbf,ashbfkasnfkasnfkasjn.fnas.fnaks.nf.kasnf.kasnf.nfskan")
                                                                                                    ^
1     E501 line too long (144 > 100 characters)
1
Error: flake8.sh failed. Aborting.
```

or

```
 docker exec basic-setup-fastapi-1 sh scripts/linters.sh
Running flake8
0
Running pylint
************* Module app.router
app/router.py:13:0: C0301: Line too long (144/100) (line-too-long)

-------------------------------------------------------------------
Your code has been rated at 9.94/10 (previous run: 10.00/10, -0.06)

Error: pylint.sh failed. Aborting.
```
