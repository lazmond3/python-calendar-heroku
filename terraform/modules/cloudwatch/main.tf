# modules/cloudwatch/main.tf
variable "name" {}
variable "schedule" {}
variable "lambda_arn" {}

# https://qiita.com/fukushi_yoshikazu/items/e68ca839e0a56152ab85
resource "aws_cloudwatch_event_rule" "event_rule" {
  name                = var.name
  schedule_expression = var.schedule
}

resource "aws_cloudwatch_event_target" "event_target" {
  rule = aws_cloudwatch_event_rule.event_rule.name
  arn  = var.lambda_arn
}

output "rule_arn" {
  value = aws_cloudwatch_event_rule.event_rule.arn
}