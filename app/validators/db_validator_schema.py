import re
from pydantic import BaseModel

from app.config import Settings


class DatabaseValidatorSchema(BaseModel):
    error: str

    def get_error_detail(self, settings: Settings) -> dict[str | int, list[str]]:
        if settings.TESTING:
            error_message, _, table_field = str(self.error).partition(":")
            column_name = table_field.split(".")[-1].lstrip()
        else:
            pattern = r"\(([^)]*)\)"
            error_message = self.error.split(":")[-1].strip()
            matches = re.findall(pattern, error_message)
            if matches:
                column_name = matches[0]
        keys = [column_name]
        values = [[error_message]]
        return dict(zip(keys, values))
