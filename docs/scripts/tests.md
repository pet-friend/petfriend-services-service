# tests.sh

### Description
Runs tests inside `/tests` directory.

### Running the command
To run the command you have to open your terminal on the main directory and run:

`sh scripts/tests.sh`

### Examples

Example of a run with all tests passing:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/tests.sh
============================= test session starts ==============================
platform linux -- Python 3.8.18, pytest-7.4.3, pluggy-1.3.0
rootdir: /app
configfile: pytest.ini
testpaths: tests
plugins: anyio-3.7.1, asyncio-0.21.1
asyncio: mode=strict
collected 1 item

tests/e2e_tests/test_health.py .                                         [100%]

============================== 1 passed in 1.08s ===============================
```

Example of a run with tests failing:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/tests.sh
============================= test session starts ==============================
platform linux -- Python 3.8.18, pytest-7.4.3, pluggy-1.3.0
rootdir: /app
configfile: pytest.ini
testpaths: tests
plugins: anyio-3.7.1, asyncio-0.21.1
asyncio: mode=strict
collected 1 item

tests/e2e_tests/test_health.py F                                         [100%]

=================================== FAILURES ===================================
______________________ TestHealth.test_get_server_health _______________________

self = <tests.e2e_tests.test_health.TestHealth testMethod=test_get_server_health>

    async def test_get_server_health(self):
        response = await self.client.get("/health")
>       assert response.status_code == 201
E       assert 200 == 201
E        +  where 200 = <Response [200 OK]>.status_code

tests/e2e_tests/test_health.py:8: AssertionError
=========================== short test summary info ============================
FAILED tests/e2e_tests/test_health.py::TestHealth::test_get_server_health - a...
============================== 1 failed in 1.02s ===============================
```