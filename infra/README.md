## Usage

The service is currently hosted on Amazon ECS, with its database on RDS.  To manage these services, the following commands have been added to the console.

```bash
# Service:
poetry run lqconsole cloud service up [--task-count=1]
poetry run lqconsole cloud service down

# Database:
poetry run lqconsole cloud database up
poetry run lqconsole cloud database down
poetry run lqconsole cloud database status

# Load Balancer:
Not yet implemented.
```
