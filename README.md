# *This repo is deprecated*
----



# periodic-rds-push
Lambda application for periodically pulling from Amazon SQS and feeding to an RDS instance

# Setup
Getting the Lambda instance to operate correctly requires some setup, primarily around configuring an AWS VPC 
instance for the Lambda and RDS instance.

The general order of operations should be as follows:

- Create an RDS instance.  
  I used the AWS webui to create an RDS instance. The instance was automatically created with 3 subnets (since 
  I was doing it in `eu-central-1`, this was 1 subnet per availabilty zone).

- In the `zappa_settings.json` add the `vpc_config` field and populate it with the `SubnetIds` and `SecurityGroupids`  
  The subitems are just the security group and subnets that the webui created for the RDS:
  ```
  "vpc_config" : {
      "SubnetIds": [
          "subnet-b34237c9",
          "subnet-1e092076",
          "subnet-affbd0e5"
      ],
      "SecurityGroupIds": [ "sg-1c93fb77" ]
  }
  ```

- Add the S3 endpoint to the VPC  
  This is done in the VPC config within the webui: VPC Dashboard > Endpoints > Create Endpoint and then follow the instructions

- Create NAT Gateway instance + Elastic IP  
  This is where it starts to get convoluted. You need the NAT Gateway to handle address translation for the public/private
  subnets you're about to create.
  
- Create a new subnet  
  This will be our new public subnet

- Create a new route table and move the internet gateway to it  
  The new route table needs to have `0.0.0.0/0` associated with the internet gateway to route properly

- Change the 3 existing subnets to use the NAT Gateway  
  Now we change the the ones the RDS wizard created to use the NAT Gateway instance.
  
Hopefully with this done you should have:
1. a Zappa profile that launches Lambdas in the private subnets,
2. a connection to S3 via the VPC Endpoint for the service,
3. access to the RDS since it's in the same subnet,
4. access to the internet to access other AWS resources such as SQS.

# Further Reading
There were two guides that were invaluable for working this out:
[This gist][1] from @reggi which details the ins and outs of VPC config and [this walkthrough][2] from @edgarroman 
detailing the database connection tricks.

[1]: https://gist.github.com/reggi/dc5f2620b7b4f515e68e46255ac042a7
[2]: https://edgarroman.github.io/zappa-django-guide/walk_app/

# Warts
There are a few downsides to this setup, two of which caused me grief. The first was that the RDS is now not accessible
from the internet. To get around this in the short term you can edit the route table for the private subnets and add the 
internet gateway as the `0.0.0.0/0` route again, opening it up. This will obviously mess with the Lambda's ability to 
access database so it's not advisable. Secondly, it requires a NAT Gateway instance, which along with the Elastic IP is 
not free; this is the primary reason for me deprecating this project for my usecase, since I'm trying to operate within 
the limits of the AWS Free Tier.
