import pytest

from app.models.addresses import AddressCreate, AddressType
from app.models.constants.addresses import MISSING_APARTMENT_MSG
from tests.factories.address_factories import AddressCreateFactory


class TestAddressesModel:
    def setup_method(self) -> None:
        self.address = AddressCreateFactory.build(type="other", country_code="AR").model_dump(
            mode="json"
        )

    @pytest.mark.asyncio
    async def test_apartment_is_required_when_type_is_apartment(self) -> None:
        # Given
        self.address["type"] = AddressType.APARTMENT
        self.address.pop("apartment", None)

        # When
        with pytest.raises(ValueError) as context:
            AddressCreate.model_validate(self.address)

        # Then
        assert MISSING_APARTMENT_MSG in str(context.value)

    @pytest.mark.asyncio
    async def test_apartment_is_none_when_type_is_not_apartment(self) -> None:
        # Given
        self.address["type"] = "house"
        self.address["apartment"] = "1A"

        # When
        add = AddressCreate.model_validate(self.address)

        # Then
        assert add.apartment is None

    @pytest.mark.asyncio
    async def test_country_code_must_be_valid(self) -> None:
        # Given
        self.address["country_code"] = "ZZ"

        # When
        with pytest.raises(ValueError) as context:
            AddressCreate.model_validate(self.address)

        # Then
        assert "Invalid country alpha2 code" in str(context.value)
