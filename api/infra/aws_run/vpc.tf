data "aws_vpc" "main" {
  tags = {
    Name = "${var.project_name}-vpc"
  }
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
}

data "aws_security_group" "default" {
  name   = "default"
  vpc_id = data.aws_vpc.main.id
}

data "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-ecs-task-role"
}