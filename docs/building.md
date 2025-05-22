## Building and Testing

Being simultaneously a console application, megalith, and micro-ish-service at the same time makes things a bit tedious to test and operate in all modes at the moment.

Again, this is just for more reference lest I forget.

```zsh
# If any dependency has changed:
poetry lock
poetry install

# Database, if not already up and initialized:
docker-compose up
poetry run lqconsole database init

# Service, if running locally:
poetry run lqconsole webservice start

# Service, if running containerized:
docker build -t lqs-test:<IMAGE_TAG> .
docker run -it --rm --network=<parent-dir>_lqnet -e OPENAI_API_KEY=$OPENAI_API_KEY -e DB_HOST=database -p 8080:8080 lqs-test:<IMAGE_TAG>

# Test with any API testing tool of your choice.
```

This will all be automated later.