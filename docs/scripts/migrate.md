# migrate.sh

### Description
Runs migrations already created. To create a migration see [make_migrations](make_migrations.md).

### Running the command
To run the command you have to open your terminal on the main directory and run:

`sh scripts/migrate.sh`

### Examples

Example of a successfull run:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/migrate.sh
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 484d2c651279, empty message
```

Example of a run without migrations:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/migrate.sh
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
```