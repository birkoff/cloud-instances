resource "aws_route53_zone" "public" {
  name    = "${lookup(var.domain_names, var.environment)}"
  comment = "public zone"
  tags = {
    Environment = "${var.environment}"
  }
}

resource "aws_route53_record" "public-ns" {
  provider = "aws.ops"
  zone_id  = "${lookup(var.hosted_zones, var.environment)}"
  name     = "${lookup(var.domain_names, var.environment)}"
  type     = "NS"
  ttl      = "30"

  records = [
    "${aws_route53_zone.public.name_servers.0}",
    "${aws_route53_zone.public.name_servers.1}",
    "${aws_route53_zone.public.name_servers.2}",
    "${aws_route53_zone.public.name_servers.3}",
  ]
}

resource "aws_acm_certificate" "cert" {
  domain_name       = "${format("api.%s", lookup(var.domain_names, local.environment))}"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "record_validation" {
  name    = "${aws_acm_certificate.cert.domain_validation_options.0.resource_record_name}"
  type    = "${aws_acm_certificate.cert.domain_validation_options.0.resource_record_type}"
  zone_id = "${aws_route53_zone.public.id}"
  records = ["${aws_acm_certificate.cert.domain_validation_options.0.resource_record_value}"]
  ttl     = 60
}

output "hosted_zone_id" {
  value = "${aws_route53_zone.public.zone_id}"
}
