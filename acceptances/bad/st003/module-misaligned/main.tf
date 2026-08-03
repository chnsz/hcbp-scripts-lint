module "network" {
  source = "./modules/network"

  vpc_id = module.vpc.id
  subnet_cidr = var.subnet_cidr
  availability_zone = var.availability_zone
}
