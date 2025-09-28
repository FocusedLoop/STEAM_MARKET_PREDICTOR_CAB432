resource "aws_s3_bucket" "assets" {
  bucket = "${var.project_name}-a2-pairs-5-a2-ml-models-s3-bucket"

  tags = {
    Project = var.project_name
  }
}
