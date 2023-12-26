# How to create new models

### Steps

1. Create a file inside the `/app/models/` directory with the name of the table.
    - Example: `/app/models/users.py`
2. Create the model.
    - Example: 
    ```
    from typing import Optional
    from sqlmodel import Field
    from app.models.util import TimestampModel, UUIDModel


    class User(UUIDModel, TimestampModel, table=True):
        __tablename__ = 'users'

        email: str = Field(unique=True)
        nickname: str
        first_name: str
        last_name: str
        age:  Optional[int] = None

    ```

3. Add the the model to the `/alembic/env.py` (If only a column was added skip this step)
    - Example: `from app.models.users import User`

4. Run the `scripts/make_migrations.sh` command. See [make_migrations](../scripts/make_migrations.md).

5. Run the `scripts/make_migrations.sh` command. See [migrate](../scripts/migrate.md).
