resource "aws_dynamodb_table" "members" {
  name         = "${local.title}-members"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "Email"

  attribute {
    name = "Email"
    type = "S"
  }

  attribute {
    name = "SubscriptionId"
    type = "S"
  }

  global_secondary_index {
    name            = "SubscriptionIdIndex"
    hash_key        = "SubscriptionId"
    range_key       = "Email"
    projection_type = "ALL"
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
  range_key    = "Datetime"

  attribute {
    name = "Datetime"
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


# {
#     "week_day": "Tue, Jan 16",
#     "date": "January 16th, 2024",
#     "title": "Toddlers (1-4)",
#     "start": "10:00",
#     "end": "12:00",
#     "location": {
#         "name": "Wijkcentrum Alleman",
#         "address": "Den Bloeyenden Wijngaerdt 1, 1183 JM Amstelveen",
#     },
#     "max_capacity": 10,
#     "spots_available": 3,
# }