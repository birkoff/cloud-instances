# EC2 Manager 
a complete eco-system for Infrastructure as a Service for AWS EC2 Instances

## Mission
The Over-All Goal is to eliminate the necessity of Engineers creating tickets requesting Infrastructure or Manually creating resources by providing an Internal API and a Front-End and serve these requirements as a Service

The EC2 Manager Front-End aims to help on having a better overview of the instances we use for temporary purposes and add policies like Termination Date and Stop at night

You don't need to be logged in into AWS to use it, only need to be in the VPN

he point is that if the Instance is listed in the page it will be controlled by our policies


## Features
### Create an App/Platform Instance
- Instance and DNS endpoints should be ready to use within 10 min
- Performs validations for duplicated name, etc
- Creates EC2 Instance with appropriate Network settings
- VPC/Subnet
- SecurityGroups
- Creates Route53 private and public records
- Executes init script which setups the "dev" user and injects our ssh keys into it
- Executes install-platform-test installation script to deploy the app/platform


### Create EC2 Instance
- Instance and DNS endpoints should be ready to use within 5 min
- Performs validations for duplicated name, etc
- Creates EC2 Instance with appropriate Network settings
- VPC/Subnet
- SecurityGroups
- Creates Route53 private and public records
- Executes init script which setups the "dev" user and injects our ssh keys into it

## Backup EC2 Instance/Create AMI 
- Creates a complete Image of the Instance including all Data Volumes


## Change State EC2 Instances
### Start:
- Creates Route53 private and public records
- Starts the Instance

### Stop:
- Removes Route53 private and public records
- Stops the Instance

### Terminate:
- Removes Route53 private and public records
- Terminates the Instance


## Update EC2 Instance
- name # perform duplicated name validation
- owner
- environment
- terminate_date
- terminate_time
- stop_time
- start_time
- Updates Route53 private and public records id name was updated

### Scheduled Stop Time
Scheduled Function which executes every hour, queries for instance with tag: StopTime with the "int" value of the current UTC hour and executes in batch the Stop EC2 Instance action


### Scheduled Start Time
Scheduled Function which executes every hour, queries for instance with tag: StartTime with the "int" value of the current UTC hour and executes in batch the Start EC2 Instance action


### Scheduled Termination Date
Scheduled Function which executes every hour, queries for instance with tag: TerminateDate & TerminateTime with the "string" value of the current date and the "int" value of the current UTC hour and executes in batch the Terminate EC2 Instance action