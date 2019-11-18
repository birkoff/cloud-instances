variable "environment" {
  type = "string"
}

variable "region" {
  type = "string"
  default = "eu-central-1"
}

variable "domain_names" {
  type = "map"
}

variable "hosted_zones" {
  type = "map"
}
