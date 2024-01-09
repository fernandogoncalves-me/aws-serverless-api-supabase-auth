import boto3

class AWS:
  def __init__(self) -> None:
    self.session = boto3.session.Session()

  def get_ssm_parameter(self, name: str, with_decryption: bool = True) -> str:
    return self.session.client("ssm").get_parameter(
      Name=name,
      WithDecryption=with_decryption
    )["Parameter"]["Value"]
