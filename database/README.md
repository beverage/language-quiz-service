## Usage

These will never have to be manually run for any local runs using docker-compose.  Running in the cloud at this time is another story.  To bootstrap the service, assuming you already have a properly configured Postgres database in RDS:

```bash
psql -U <user> -h <public endpoint> -p <port> < database/0-CreateDatabase.sql 
psql -U <user> -h <public endpoint> -p <port> < database/1-CreateTables.sql 
```

Setting up an RDS instance is right now a manual process, and far short of what it should, or would if this was a production service, be.  Here is how to do it while remaining in the free tier.  This is mostly just for my reference.  Just use docker-compose and run it locally if you're actually reading this.

1. Go to 'Aurora and RDS', and select 'Create database'.
1. Make sure 'Free Tier' is selected, and zero extra features are selected as well.
1. Check 'Yes' for public access.
1. Select password authentication, and let AWS automatically generate one.  _Don't forget to copy it from the confirmation screen._
    - Choose another username if you like.
1. While it is being created, add or update the Github secret that also contains it.
1. If the endpoint is changing, update any relevant CNAME record that point to it.
1. Wait a bit until all processes complete.  Test with a simple psql connection.

This can obviously be improved.
