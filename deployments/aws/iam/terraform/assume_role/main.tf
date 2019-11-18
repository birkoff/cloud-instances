resource "aws_iam_role" "role" {
  name        = "cloud-machines-assume-role-${var.environment}"
  description = "cloud-machines-assume-role-${var.environment}"
  path        = "/ec2manager/"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": ["arn:aws:iam::${var.principal_account_id}:root"]
      },
      "Action": "sts:AssumeRole",
      "Condition": {}
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "policy" {
  name = "cloud-machines-assume-role-policy-${var.environment}"
  role = "${aws_iam_role.role.id}"

  policy = <<EOP
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowToManageServices",
            "Effect": "Allow",
            "Action": [
                "ec2:*",
                "route53:*",
                "tag:*",
                "iam:PassRole",
                "sns:Publish"
            ],
            "Resource": "*"
        }
    ]
}
EOP
}