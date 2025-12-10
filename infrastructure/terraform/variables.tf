# Terraform Variables for MedAssureAI Infrastructure

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table for artifacts"
  type        = string
  default     = "MedAssureAI_Artifacts"
}

variable "kms_key_arn" {
  description = "ARN of KMS key for encryption (optional)"
  type        = string
  default     = ""
}

variable "sns_topic_arn" {
  description = "ARN of SNS topic for alarms (optional)"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Project name for tagging"
  type        = string
  default     = "MedAssureAI"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project   = "MedAssureAI"
    ManagedBy = "Terraform"
  }
}
