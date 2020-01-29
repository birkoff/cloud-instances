import boto3
from boto3 import Session
from botocore.exceptions import ClientError
import modules.logs as logs


def assume_role_session(account_name, role, region):
    client = boto3.client("sts")
    logs.info(
        "assume_role_session",
        "client.assume_role(RoleArn={}, RoleSessionName={}, Region={})".format(
            role, account_name, region
        ),
    )
    try:
        response = client.assume_role(RoleArn=role, RoleSessionName=account_name)
    except ClientError as error:
        raise Exception(
            "An error occurred when calling the AssumeRole operation: Access denied to role {}".format(
                role
            )
        )

    return Session(
        aws_access_key_id=response["Credentials"]["AccessKeyId"],
        aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
        aws_session_token=response["Credentials"]["SessionToken"],
        region_name=region,
    )


if __name__ == "__main__":
    pass
