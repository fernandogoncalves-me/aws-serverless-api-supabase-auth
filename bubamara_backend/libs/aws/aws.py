import decimal

import boto3

class AWS:
  def __init__(self) -> None:
    self.session = boto3.session.Session()

  def get_ssm_parameter(self, name: str, with_decryption: bool = True) -> str:
    return self.session.client("ssm").get_parameter(
      Name=name,
      WithDecryption=with_decryption
    )["Parameter"]["Value"]

  def delete_ddb_item(self, table_name: str, key: dict) -> None:
    return self.session.resource("dynamodb").Table(table_name).delete_item(Key=key, ReturnValues="ALL_OLD")
  
  def get_ddb_item(self, table_name: str, key: dict) -> dict:
    item = self.session.resource("dynamodb").Table(table_name).get_item(Key=key).get("Item", None)
    if item:
      for attrib, value in item.items():
        if isinstance(value, decimal.Decimal):
          item[attrib] = int(value)
        if isinstance(value, set):
          item[attrib] = list(value)

    return item
  
  def put_ddb_item(self, table_name: str, params: dict) -> None:
    return self.session.resource("dynamodb").Table(table_name).put_item(**params)

  def query_ddb_items(self, table_name: str, params: dict) -> dict:
    return self.session.resource("dynamodb").Table(table_name).query(**params)["Items"]

  def update_ddb_item(self, table_name: str, params: dict) -> None:
    return self.session.resource("dynamodb").Table(table_name).update_item(**params)
  
  def transact_write_items(self, transact_items: list) -> None:
    return self.session.client("dynamodb").transact_write_items(TransactItems=transact_items)
  