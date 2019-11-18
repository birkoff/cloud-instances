provider "aws" {
  alias  = "engineering-prod"
  region = local.vpc_regions["frankfurt"]

  assume_role {
    role_arn = "arn:aws:iam::${local.account_ids["engineering-prod"]}:role/${var.role_arn}"
  }
}

module "iam-sts-assume-role-engineering-prod" {
  providers = {
    aws = aws.engineering-prod
  }

  source               = "./assume_role"
  principal_account_id = local.account_ids[local.account_name]
  environment          = local.environment
}

output "iam_sts_assumerole_engineering_prod" {
  value = module.iam-sts-assume-role-engineering-prod.sts_assume_role
}

