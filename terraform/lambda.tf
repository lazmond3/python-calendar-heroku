
variable app_name {
  default = "pylib_google_calendar_line_bot"
}
# Function
resource "aws_lambda_function" "pylib_google" {
  function_name = "${var.app_name}"

  handler                        = "main.lambda_handler"
  filename                       = "${data.archive_file.function_zip.output_path}"
  runtime                        = "python3.9"
  role                           = "${aws_iam_role.lambda_iam_role.arn}"
  source_code_hash               = "${data.archive_file.function_zip.output_base64sha256}"
  layers = ["${aws_lambda_layer_version.lambda_layer.arn}"]

  environment {
       variables = {
          G_SECRET = "${var.G_SECRET}"
          CALENDAR_ID = "${var.CALENDAR_ID}"
          LINE_BOT_CHANNEL_ACCESS_TOKEN = "${var.LINE_BOT_CHANNEL_ACCESS_TOKEN}"
          LINE_BOT_CHANNEL_SECRET = "${var.LINE_BOT_CHANNEL_SECRET}"
          RYO_UID = "${var.RYO_UID}"
       }
  }
}


# Archive
# レイヤー
data "archive_file" "layer_zip" {
  type        = "zip"
  source_dir  = "../build/layer"
  output_path = "lambda/layer.zip"
}
data "archive_file" "function_zip" {
  type        = "zip"
  source_dir  = "../build/function"
  output_path = "lambda/function.zip"
}

# Layer
resource "aws_lambda_layer_version" "lambda_layer" {
  layer_name = "${var.app_name}_lambda_layer"
  filename   = "${data.archive_file.layer_zip.output_path}"
  source_code_hash = "${data.archive_file.layer_zip.output_base64sha256}"
}