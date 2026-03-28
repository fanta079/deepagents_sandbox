from fastapi import APIRouter

router = APIRouter()


@router.get("/example")
def get_example():
    return {"message": "This is an example endpoint"}


@router.post("/example")
def post_example(data: dict):
    return {"received": data}
