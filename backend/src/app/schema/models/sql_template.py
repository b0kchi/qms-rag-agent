from sqlmodel import SQLModel, Field


class SqlTemplate(SQLModel, table=True):
    id: str = Field(primary_key=True, index=True)
    name: str
    description: str
    sql_text: str
    params_json: str  # 필요한 파라미터 스키마(JSON 문자열)