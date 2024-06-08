from polyfactory.factories.pydantic_factory import ModelFactory

from app.models.reviews import ReviewCreate


class ReviewCreateFactory(ModelFactory[ReviewCreate]):
    __model__ = ReviewCreate
