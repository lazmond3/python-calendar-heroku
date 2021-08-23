terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1"
}

resource "aws_s3_bucket" "google-python-bot-calendar" {
  bucket = "google-python-bot-calendar"
  acl    = "private"

  versioning {
    enabled = true
  }

  tags = {
    Name        = "google-python-bot-calendar/tfstate"
    Environment = "Dev"
  }
}
