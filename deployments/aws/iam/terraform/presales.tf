provider "aws" {
  alias  = "presales"
  region = local.vpc_regions["frankfurt"]

  assume_role {
    role_arn = "arn:aws:iam::${local.account_ids["presales"]}:role/${var.role_arn}"
  }
}

module "iam-sts-assume-role-presales" {
  providers = {
    aws = aws.presales
  }

  source               = "./assume_role"
  principal_account_id = local.account_ids[local.account_name]
  environment          = local.environment
}

output "iam_sts_assumerole_presales" {
  value = module.iam-sts-assume-role-presales.sts_assume_role
}

