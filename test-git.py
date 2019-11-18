import os
import requests
import boto3
import botocore
from jinja2 import Template
from json import loads, dumps


def get_repo_contents(path, headers):
    resp = requests.get(path, headers=headers)

    if (100 <= resp.status_code < 600) and (resp.status_code != 200):
        print(resp.url)
        raise ConnectionError('Error: Bad response', resp.status_code, resp.reason)

    contents = loads(resp.content.decode('utf-8'))

    return contents


def fetch_users(contents, root_path, headers):
    repo_url = os.environ.get('repo_url')
    repo_url = repo_url.rstrip('/') + '/'

    dirs = []

    user_keys = {}
    admin_keys = {}  # these users will be added to every instance

    for each in contents:
        if each['type'] == 'dir' and each['name'].find('public_keys') != -1:
            dir_path = root_path + each['name']
            dirs.append(get_repo_contents(dir_path, headers=headers))

    for dir in dirs:
        for file in dir:
            if file['type'] == 'dir':  # ignore subfolders
                continue

            file_path = repo_url + file['path']
            username = file['name'].split('.')[0]

            key = requests.get(file_path, headers=headers).content.decode('utf-8')

            # remove blank lines for consistency
            ssh_key = "".join([s for s in key.strip().splitlines(True) if s.strip("\r\n").strip()])

            if file['path'].find('common') != -1:
                print('Fetched Common User:', username)
                print(ssh_key)
                admin_keys[username] = ssh_key
            else:
                print('Fetched User:', username)
                print(ssh_key)
                user_keys[username] = ssh_key

    total_users = int(len(user_keys)) + int(len(admin_keys))

    print('\nTotal:  ', total_users, 'users (', len(user_keys), 'users', '+', len(admin_keys), 'admins )')

    return user_keys, admin_keys


# generate cloud init config file from jinja template
def render_template(user_keys, admin_keys):
    all_users = {**user_keys, **admin_keys}
    config_files = []
    admin_is_owner = False

    if not user_keys:
        raise Exception('ERROR: No users fetched from GitHub')

    for user, user_key in all_users.items():
        with open('init.j2') as f:
            template = Template(f.read())

        # check if owner is also admin
        for admin_key in admin_keys.values():
            if admin_key == user_key:
                admin_is_owner = True

        if admin_is_owner:  # if user is admin then just add all admin keys
            print('\nRendering config file for admin user', user, 'from template')
            config = template.render(owner=None, admins=admin_keys.values())
        else:
            print('\nRendering config file for', user, 'from template')
            config = template.render(owner=user_key, admins=admin_keys.values())

        clean_config = "".join([s for s in config.strip().splitlines(True) if s.strip("\r\n").strip()])

        conf_file = '/tmp/' + user + '.conf'
        config_files.append(conf_file)

        with open(conf_file, 'w') as f:
            f.write(clean_config)
        print('Created', conf_file)

    return config_files


# upload users.list and cloud-init configs for each user to S3
def upload_to_s3(bucket_name, files, users):
    pass
    users.sort()

    s3 = boto3.client('s3')

    users_list_path = '/tmp/users.list'
    users_list_file = users_list_path.split('/')[-1]

    print('\nCreating users.list file')
    with open(users_list_path, 'w') as f:
        f.write("\n".join(users))
    print(len(users), users)

    print('\nUploading', users_list_file, 'to', bucket_name)
    try:
        s3.upload_file(users_list_path, bucket_name, users_list_file)
    except Exception as error:
        print('Error: Upload of', users_list_path, 'Failed\n', error)
        return False
    print('Upload of', users_list_file, 'Finished')

    for file_path in files:
        filename = file_path.split('/')[-1]

        config = os.path.isfile(file_path)

        if not config:
            return False

        print('\nUploading', filename, 'to', bucket_name)
        try:
            s3.upload_file(file_path, bucket_name, filename)
        except Exception as error:
            print('Error: Upload of', file_path, 'Failed\n', error)
            return False
        print('Upload of', filename, 'Finished')

    return True


# Import github ssh keys to AWS Key Pairs
def upload_aws_key_pairs(users):
    ec2 = boto3.client('ec2')

    imported_keys = []
    existing_keys = []
    incompatible_keys = []

    print('\nSearching for new AWS key pairs to import\n')
    for user, key in users.items():
        key_name = user + '-gh-key'

        if key.find('ssh-rsa') == -1:
            print('WARNING: Cant import', key_name, '(non-RSA keys are not supported by AWS)\n', key)
            incompatible_keys.append(key_name)

        try:
            ec2.import_key_pair(
                KeyName=key_name,
                PublicKeyMaterial=key
            )
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'InvalidKeyPair.Duplicate':
                print(user, 'AWS key pair already exists (', key_name, ') Skipping...')
                existing_keys.append(key_name)
        except Exception as error:
            print('ERROR: Something went wrong during AWS key import\n', error)
            return False
        else:
            print('Importing new key:', key_name)
            imported_keys.append(key_name)

    print()
    if existing_keys:
        print(len(existing_keys), 'Existing:', existing_keys)
    if imported_keys:
        print(len(imported_keys), 'Imported:', imported_keys)
    if incompatible_keys:
        print(len(incompatible_keys), 'Incompatible:', incompatible_keys)
    if not existing_keys and not imported_keys:
        print('No Existing Keys Found and Nothing Imported')

    all_aws_keys = existing_keys + imported_keys

    all_aws_keys.sort()

    return all_aws_keys


# compare github keys and AWS key pairs and remove those that don't exist in github
def clean_aws_key_pairs(github_keys):
    if not github_keys:
        raise Exception('ERROR: No AWS key pairs found that match GitHub')

    ec2 = boto3.client('ec2')

    aws_key_pairs = []
    aws_deleted_keys = []

    resp = ec2.describe_key_pairs()
    for kn in resp['KeyPairs']:
        key_name = kn['KeyName']
        if key_name.find('-gh-key') != -1:  # we only care about keys that came from github (-gh-key in their name)
            aws_key_pairs.append(key_name)

    aws_key_pairs.sort()

    for key in aws_key_pairs:
        # remove AWS key pairs with -gh-key in their name that are not in github
        if key not in github_keys:
            print('WARNING:', key, 'not found in GitHub')
            print('Deleting:', key)
            resp = ec2.delete_key_pair(KeyName=key)
            print(resp)
            aws_deleted_keys.append(key)

    if aws_deleted_keys:
        print('Deleted Keys:', aws_deleted_keys)

    return aws_deleted_keys


def github_auth_handler(req_id):
    expected_id = str(os.environ.get('repo_id'))

    if expected_id == req_id:
        return True
    else:
        return False


def http_response(status):
    if status == 200:
        print('HTTP Status: 200')
        response = {
            'statusCode': 200,
            'body': dumps({'Status': 'SUCCESS'})
                }
    elif status == 403:
        print('HTTP Status: 403')
        response = {
            'statusCode': 403,
            'body': dumps({'Access': 'DENIED'})
            }
    else:
        print('HTTP Status: 500')
        response = {
            'statusCode': 500,
            'body': dumps({'Status': 'FAILED'})
            }

    return response


def lambda_handler(event, context):
    if context is not 'local':
        req_payload = loads(event['body'])
        req_repo_id = str(req_payload['repository']['id'])
        print(req_payload)

        authorized = github_auth_handler(req_repo_id)

        if not authorized:
            return http_response(403)
        else:
            print('Authentication Check Passed')

    dir = os.environ.get('contents_url')
    dir = dir.rstrip('/') + '/'

    github_token = os.environ.get('github_token')
    s3_bucket = os.environ.get('s3_bucket')

    hdrs = {'Authorization': 'token ' + github_token,
            'Accept': "application/vnd.github.v3.raw"}

    data = get_repo_contents(path=dir, headers=hdrs)

    users, admins = fetch_users(data, root_path=dir, headers=hdrs)

    all_keys = {**users, **admins}  # merge two dicts

    for ak in all_keys:
        print("\necho \"{}\" >> /home/$DEVUSER/.ssh/authorized_keys".format(all_keys[ak]))

    conf_files = render_template(users, admins)

    all_aws_keys = upload_aws_key_pairs(all_keys)

    if not all_aws_keys:
        return http_response(500)

    clean_aws_key_pairs(all_aws_keys)

    uploaded = upload_to_s3(s3_bucket, conf_files, users=list(all_keys.keys()))

    if uploaded:
        return http_response(200)
    else:
        return http_response(500)


if __name__ == "__main__":
    # For local testing
    os.environ['contents_url'] = "https://api.github.com/repos"
    os.environ['repo_url'] = "https://api.github.com/repos/"
    os.environ['github_token'] = ""  # initialize with a valid github token
    os.environ['s3_bucket'] = ""

    event = 'Local Test'

    lambda_handler(event, 'local')
