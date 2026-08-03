module "vpc" {
  source = "./modules/vpc"

  name = var.vpc_name
  cidr = var.vpc_cidr

  count = var.create_vpc ? 1 : 0
}

module "network" {
  source = "./modules/network"

  vpc_id            = try(module.vpc[0].id, "")
  subnet_cidr       = var.subnet_cidr
  availability_zone = var.availability_zone
}
