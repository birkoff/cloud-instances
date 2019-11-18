provider "aws" {
  alias  = "engineering-dev"
  region = local.vpc_regions["frankfurt"]

  assume_role {
    role_arn = "arn:aws:iam::${local.account_ids["engineering-dev"]}:role/${var.role_arn}"
  }
}

module "iam-sts-assume-role-engineering-dev" {
  providers = {
    aws = aws.engineering-dev
  }

  source               = "./assume_role"
  principal_account_id = local.account_ids[local.account_name]
  environment          = local.environment
}

output "iam_sts_assumerole_engineering_dev" {
  value = module.iam-sts-assume-role-engineering-dev.sts_assume_role
}

