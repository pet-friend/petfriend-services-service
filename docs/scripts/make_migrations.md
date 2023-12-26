# make_migrations.sh

### Description
Crates migrations. The migration will be saved in the `/alembic/versions/` directory

### Running the command
To run the command you have to open your terminal on the main directory and run:

`sh scripts/make_migrations.sh`

### Examples

Example of a successfull run:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/make_migrations.sh
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'users'
INFO  [alembic.autogenerate.compare] Detected added index 'ix_users_id' on '['id']'
Generating /app/alembic/versions/484d2c651279_.py ...  done
```

Example of a failed run because of pending migration:

```
git:(main) ✗ docker exec basic-setup-fastapi-1 sh scripts/make_migrations.sh
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
ERROR [alembic.util.messaging] Target database is not up to date.
FAILED: Target database is not up to date.
```