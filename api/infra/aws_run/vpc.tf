# Use the actual VPC from your instance
data "aws_vpc" "main" {
  id = "vpc-007bab53289655834"
}

# Get subnets in that VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.main.id]
  }
}

# Use the CAB432SG security group from your instance
data "aws_security_group" "default" {
  id = "sg-032bd1ff8cf77dbb9"
}

# Use the existing IAM role from your instance
data "aws_iam_role" "ecs_execution" {
  name = "CAB432-Instance-Role"
}

data "aws_iam_role" "ecs_task" {
  name = "CAB432-Instance-Role"
}