resource "aws_dynamodb_table" "leads" {
  name         = "${local.title}-leads"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "Email"

  attribute {
    name = "Email"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "members" {
  name         = "${local.title}-members"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "MemberID"

  attribute {
    name = "Email"
    type = "S"
  }

  attribute {
    name = "SubscriptionType"
    type = "S"
  }

  attribute {
    name = "MemberID"
    type = "S"
  }

  global_secondary_index {
    name            = "SubscriptionTypeIndex"
    hash_key        = "SubscriptionType"
    range_key       = "MemberID"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "EmailIndex"
    hash_key        = "Email"
    projection_type = "KEYS_ONLY"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "sessions" {
  name         = "${local.title}-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "SessionType"
  range_key    = "SessionDatetime"

  attribute {
    name = "SessionDatetime"
    type = "S"
  }

  attribute {
    name = "SessionType"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "reservations" {
  name         = "${local.title}-reservations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "Email"
  range_key    = "ReservationType"

  attribute {
    name = "Email"
    type = "S"
  }

  attribute {
    name = "ReservationType"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = local.tags
}
