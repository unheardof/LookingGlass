# LookingGlass
A collaborative network / infrastructure visualization tool oriented towards use for defensive and offensive cyber operations

# How to run

From the command line, execute:

> FLASK_APP=application.py flask run

This will make the application accessible locally at http://127.0.0.1:5000

To make the application accessible to other computers, add `--host=0.0.0.0` to the end of the command 

> FLASK_APP=application.py flask run --host=0.0.0.0

**Note:** this is not recommended for production use and exposing a local webserver on your machine over the network has potential security considerations. Please do this with care.


# How to run on ElasticBeanstalk

1. Set the LOCAL_MODE value to False (this will cause the graph state to be stored in S3 instead of locally on the ElasticBeanstalk instance, which is empheral)
1. Create an AWS account
1. Install and configure the AWS CLI
1. From the root LookingGlass direcctory (i.e. where the root of the local LookingGlass git repository) run `eb init -p python-3.6 <application name> --region <AWS region where the applicaiton should be hosted>`
1. Create an environment within your application by running `eb create <environment name>`
1. Open the application by running `eb open`

**Note:** you will be billed for all AWS infrastructure used will the application / environment are active; to stop the application, run `eb terminate <environment name>`
See [this page](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html) for more details
