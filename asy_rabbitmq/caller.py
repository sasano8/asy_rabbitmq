from pydantic import BaseModel, Field
from fastapi.encoders import jsonable_encoder
from json import dumps


class CallInfo(BaseModel):
    func: str = Field(description="実行する関数")
    # args: tuple = Field(description="実行する関数に渡す位置引数")
    kwargs: dict = Field(description="実行する関数に渡すキーワード引数")

    def encode(self) -> str:
        dic = jsonable_encoder(self)
        return dumps(dic, ensure_ascii=False)