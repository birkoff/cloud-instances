terraform {
  required_version = ">= 0.12"

  backend "remote" {
    hostname     = "app.terraform.io"
    organization = ""

    workspaces {
      prefix = "cloud-machines-api-assumerole-accounts-"
    }
  }
}

data "terraform_remote_state" "variables" {
  backend = "remote"

  config = {
    organization = ""
    workspaces = {
      name = "global-variables"
    }
  }
}

data "terraform_remote_state" "accounts" {
  backend = "remote"

  config = {
    organization = ""

    workspaces = {
      name = "master-organisation-accounts"
    }
  }
}

locals {
  environment = var.environment
  account_ids  = "${tomap(data.terraform_remote_state.accounts.outputs.account_ids)}"
  account_name = format("engineering-%s", var.environment)
  vpc_regions  = tomap(data.terraform_remote_state.variables.outputs.vpc_regions)
  vpc_peering_ids  = tomap(data.terraform_remote_state.variables.outputs.vpc_peering_ids)
}

provider "aws" {
  alias  = "main"
  region = "${lookup(local.vpc_regions, "frankfurt")}"
}

variable role_arn {
  type = "string"
}

provider "aws" {
  alias  = "ops"
  region = local.vpc_regions["frankfurt"]

  assume_role {
    role_arn = "arn:aws:iam::${local.account_ids["operations-prod"]}:role/${var.role_arn}"
  }
}

provider "aws" {
  region = local.vpc_regions["frankfurt"]

  assume_role {
    role_arn = "arn:aws:iam::${local.account_ids[local.account_name]}:role/${var.role_arn}"
  }
}

