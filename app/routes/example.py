from typing import Sequence, NoReturn
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from ..repositories.example import ExampleCrud
from ..models.example import ExampleCreate, ExampleRead

router = APIRouter(prefix="/example", tags=["Example"])


def _not_found(example_id: str) -> NoReturn:
    raise HTTPException(
        status_code=http_status.HTTP_404_NOT_FOUND,
        detail=f"Example with id {example_id} not found",
    )


@router.get("/", status_code=http_status.HTTP_200_OK)
async def get_examples(
    repo: ExampleCrud = Depends(ExampleCrud), skip: int = 0, limit: int | None = None
) -> Sequence[ExampleRead]:
    return await repo.get_all(skip=skip, limit=limit)


@router.post("/", status_code=http_status.HTTP_201_CREATED)
async def create_example(
    data: ExampleCreate, repo: ExampleCrud = Depends(ExampleCrud)
) -> ExampleRead:
    example = await repo.create(data)
    return example


@router.get("/{example_id}", status_code=http_status.HTTP_200_OK)
async def get_example_by_id(
    example_id: str, repo: ExampleCrud = Depends(ExampleCrud)
) -> ExampleRead:
    example = await repo.get_by_id(example_id)

    if not example:
        _not_found(example_id)

    return example


@router.put("/{example_id}", status_code=http_status.HTTP_200_OK)
async def put_example(
    example_id: str,
    data: ExampleCreate,
    repo: ExampleCrud = Depends(ExampleCrud),
) -> ExampleRead:
    try:
        return await repo.update(example_id, data.model_dump())
    except ValueError:
        _not_found(example_id)


@router.delete("/{example_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_example_by_id(
    example_id: str, example: ExampleCrud = Depends(ExampleCrud)
) -> None:
    await example.delete(example_id)
