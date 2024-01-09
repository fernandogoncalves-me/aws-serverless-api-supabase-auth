resource "aws_iam_role" "this" {
  name = var.title

  assume_role_policy = file("${path.module}/files/iam/assume_role_policy.json")
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.this.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "custom" {
  count = var.iam_policy != null ? 1 : 0

  name   = var.title
  policy = var.iam_policy
  role   = aws_iam_role.this.id
}
