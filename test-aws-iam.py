import boto3

client = boto3.client('iam')

response = client.list_users(
    PathPrefix='/engineering/',
)

users = []
ssh_keys = []

for user in response.get('Users'):
    user_data = {}

    tresponse = client.list_user_tags(
        UserName=user.get('UserName')
    )

    user_tags = []
    for tags in tresponse.get('Tags'):
        if tags.get('Key') == 'Name':
            user_name = tags.get('Value')
            break

    kidresponse = client.list_ssh_public_keys(
        UserName=user.get('UserName')
    )

    user_ssh_key_id = None
    for ssh_keys_ids in kidresponse.get('SSHPublicKeys'):
        user_ssh_key_id = ssh_keys_ids.get('SSHPublicKeyId')
        break

    user_ssh_key = None
    if user_ssh_key_id:
        kresponse = client.get_ssh_public_key(
            UserName=user.get('UserName'),
            SSHPublicKeyId=user_ssh_key_id,
            Encoding='SSH'
        )

        user_ssh_key = kresponse.get('SSHPublicKey').get('SSHPublicKeyBody')

    user_data = {
        'username': user.get('UserName'),
        'name': user_name,
        'pub_ssh_key': user_ssh_key,
        'path': user.get('Path'),
        # 'groups': ''
    }

    if user_ssh_key:
        ssh_keys.append(user_ssh_key)

for k in ssh_keys:
    print("\necho \"{}\" >> /home/$DEVUSER/.ssh/authorized_keys".format(k))
