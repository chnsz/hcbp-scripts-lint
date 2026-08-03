module "vpc" {
  source = "./modules/vpc"

  name = var.vpc_name
  cidr = var.vpc_cidr

  count             = var.create_vpc ? 1 : 0
}
