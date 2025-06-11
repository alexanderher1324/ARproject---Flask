provider "aws" {
  region = "us-east-1" # Change to your desired region
}

# Security Group for EC2 (allows SSH)
resource "aws_security_group" "ec2_sg" {
  name        = "ec2_sg"
  description = "Allow SSH"
  vpc_id      = "vpc-08e541964ac42ff77" 

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["192.168.1.12/32"] 
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Security Group for RDS (allows EC2 + optional laptop IP)
resource "aws_security_group" "rds_sg" {
  name        = "rds_sg"
  description = "Allow PostgreSQL access from EC2 and laptop"
  vpc_id      = "vpc-08e541964ac42ff77" # replace with your VPC ID

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id] # EC2 SG allowed
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["192.168.1.12/32"] # Optional: your IP to test with pgAdmin or psql
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Key pair (change this if you already have one)
resource "aws_key_pair" "deployer_key" {
  key_name   = "deployer-key"
  public_key = file("~/.ssh/id_rsa.pub") # Adjust path to your public key
}

# EC2 Instance
resource "aws_instance" "arproject_ec2" {
  ami                         = "ami-051f7e7f6c2f40dc1" # Amazon Linux 2023 AMI (for us-east-1), change if using another region
  instance_type               = "t3.micro"
  key_name                    = aws_key_pair.deployer_key.key_name
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  associate_public_ip_address = true
  subnet_id                   = "subnet-01dd5ce5f4440d2df" 

  tags = {
    Name = "arproject-ec2"
  }
}

# RDS PostgreSQL instance
resource "aws_db_instance" "arproject_postgres" {
  identifier              = "arproject-postgres-db"
  allocated_storage       = 20
  engine                  = "postgres"
  engine_version          = "15.4" # adjust if needed
  instance_class          = "db.t3.micro"
  name                    = "arproject" # initial DB name
  username                = "admin"
  password                = "YourStrongPassword123!"
  vpc_security_group_ids  = [aws_security_group.rds_sg.id]
  skip_final_snapshot     = true
  publicly_accessible     = true
  backup_retention_period = 7

  tags = {
    Name = "arproject-postgres-db"
  }
}

# Outputs
output "ec2_public_ip" {
  value = aws_instance.arproject_ec2.public_ip
}

output "rds_endpoint" {
  value = aws_db_instance.arproject_postgres.endpoint
}
