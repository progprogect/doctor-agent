terraform {
  backend "s3" {
    bucket         = "doctor-agent-terraform-state-760221990195"
    key            = "mvp/terraform.tfstate"
    region         = "me-central-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}







