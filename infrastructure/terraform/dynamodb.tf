# DynamoDB Table for MedAssureAI Artifacts
# Single-table design with composite keys for efficient querying

resource "aws_dynamodb_table" "medassure_artifacts" {
  name           = var.dynamodb_table_name
  billing_mode   = "PAY_PER_REQUEST" # On-demand billing for variable workloads
  hash_key       = "PK"
  range_key      = "SK"

  # Primary Key Attributes
  attribute {
    name = "PK"
    type = "S" # Partition Key: PROJECT#<project_id>
  }

  attribute {
    name = "SK"
    type = "S" # Sort Key: <entity_type>#<entity_id> or METADATA
  }

  # GSI Attributes for reverse lookup
  attribute {
    name = "GSI1PK"
    type = "S" # <entity_type>#<entity_id>
  }

  attribute {
    name = "GSI1SK"
    type = "S" # PROJECT#<project_id>
  }

  # Global Secondary Index for direct artifact lookup
  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }

  # Enable point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = true
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  # Enable TTL for session cleanup (optional)
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Tags for resource management
  tags = {
    Name        = "MedAssureAI Artifacts Table"
    Environment = var.environment
    Project     = "MedAssureAI"
    ManagedBy   = "Terraform"
  }
}

# CloudWatch alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "dynamodb_read_throttle" {
  alarm_name          = "${var.dynamodb_table_name}-read-throttle"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ReadThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors DynamoDB read throttle events"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    TableName = aws_dynamodb_table.medassure_artifacts.name
  }
}

resource "aws_cloudwatch_metric_alarm" "dynamodb_write_throttle" {
  alarm_name          = "${var.dynamodb_table_name}-write-throttle"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "WriteThrottleEvents"
  namespace           = "AWS/DynamoDB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors DynamoDB write throttle events"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    TableName = aws_dynamodb_table.medassure_artifacts.name
  }
}

# Output the table name and ARN
output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.medassure_artifacts.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.medassure_artifacts.arn
}
