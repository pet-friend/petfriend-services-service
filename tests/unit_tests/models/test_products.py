from unittest import IsolatedAsyncioTestCase

from pydantic import ValidationError
from app.models.products import Category, ProductCreate
from tests.factories.product_factories import ProductCreateFactory

import pytest


class TestProductsModel(IsolatedAsyncioTestCase):
    async def test_product_create_with_all_fields(self) -> None:
        # Given
        product_create = ProductCreateFactory.build()
        # When
        product_created = ProductCreate(**product_create.__dict__)
        # Then
        assert product_created == product_create

    async def test_product_create_with_required_fields(self) -> None:
        # Given
        product_create = ProductCreateFactory.build()
        product_create.description = None  # type: ignore
        product_create.available = None  # type: ignore
        # When
        product_created = ProductCreate(**product_create.__dict__)
        # Then
        assert product_created == product_create

    async def test_product_create_without_some_required_fields(self) -> None:
        # Given
        product_create = ProductCreateFactory.build()
        product_create.name = None  # type: ignore
        # When
        with self.assertRaises(ValidationError) as context:
            ProductCreate(**product_create.__dict__)
        # Then
        assert "valid string" in str(context.exception)

    async def test_product_create_with_invalid_categories(self) -> None:
        # Given
        product_create = ProductCreateFactory.build()
        # When
        with self.assertRaises(ValueError) as context:
            product_create.categories = [Category("invalid")]
            ProductCreate(**product_create.__dict__)
        # Then
        assert "is not a valid Category" in str(context.exception)

    async def test_product_create_with_too_many_categories(self) -> None:
        # Given
        product_create = ProductCreateFactory.build()
        product_create.categories.append(Category("camas"))
        product_create.categories.append(Category("platos_y_comederos"))
        product_create.categories.append(Category("cuchas"))
        # When
        with self.assertRaises(ValueError) as context:
            ProductCreate(**product_create.__dict__)
        # Then
        assert "Cannot have more than" in str(context.exception)
