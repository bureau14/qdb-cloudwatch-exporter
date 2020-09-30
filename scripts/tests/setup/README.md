# qdb-test-setup

The goal of this project is to provide reusable test setup to run and stop qdbd instances.
It can run on any platform as long as it is run in bash.

Its functions are simple:
1. Find quasardb binaries
1. Create public and private keys for the server
1. Add a user
1. Run qdbd in insecure mode
1. Run qdbd in secure mode
1. Stop qdbd instances reliably
1. Log everything and provide static paths for the artifacts

The expected path for the binaries is: `./qdb/bin`

## Run
`./start-services.sh`

## Stop
`./stop-services.sh`

## Cleanup
In the case you would like to fully cleanup after use (stop does not remove everything), you can use this command:

`bash -c "source ./cleanup.sh && full_cleanup"`
