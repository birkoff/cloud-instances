output "sts_assume_role" {
  value = "${aws_iam_role.role.arn}"
}
