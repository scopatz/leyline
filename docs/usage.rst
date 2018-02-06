Fixie Command Line Usage
========================
The fixie command line interface is as follows:

.. code-block:: bash

    $ fixie --help
    usage: fixie [-h] [-p PORT] [--config-dir FIXIE_CONFIG_DIR]
                 [--data-dir FIXIE_DATA_DIR] [--jobs-dir FIXIE_JOBS_DIR]
                 [--jobid-file FIXIE_JOBID_FILE]
                 [--job-aliases-file FIXIE_JOB_ALIASES_FILE]
                 [--holding-time FIXIE_HOLDING_TIME] [--njobs FIXIE_NJOBS]
                 [--logfile FIXIE_LOGFILE] [--sims-dir FIXIE_SIMS_DIR]
                 [--paths-dir FIXIE_PATHS_DIR] [--data-url FIXIE_DATA_URL]
                 [--creds-url FIXIE_CREDS_URL] [--batch-url FIXIE_BATCH_URL]
                 [--creds-dir FIXIE_CREDS_DIR]
                 [--completed-jobs-dir FIXIE_COMPLETED_JOBS_DIR]
                 [--failed-jobs-dir FIXIE_FAILED_JOBS_DIR]
                 [--canceled-jobs-dir FIXIE_CANCELED_JOBS_DIR]
                 [--queued-jobs-dir FIXIE_QUEUED_JOBS_DIR]
                 [--running-jobs-dir FIXIE_RUNNING_JOBS_DIR]
                 services [services ...]

    Cyclus-as-a-Service

    positional arguments:
      services              the services to start, may be "all" to specify all
                            installed services. Default is "all" Allowed values
                            are: all, batch, creds, data

    optional arguments:
      -h, --help            show this help message and exit
      -p PORT, --port PORT  port to serve the fixie services on.
      --config-dir FIXIE_CONFIG_DIR
                            Path to fixie configuration directory
      --data-dir FIXIE_DATA_DIR
                            Path to fixie data directory
      --jobs-dir FIXIE_JOBS_DIR
                            Path to fixie jobs directory
      --jobid-file FIXIE_JOBID_FILE
                            Path to the fixie job file, which contains the next
                            jobid.
      --job-aliases-file FIXIE_JOB_ALIASES_FILE
                            Path to the fixie job names file, which contains
                            aliases associated with users, projects, and jobids.
      --holding-time FIXIE_HOLDING_TIME
                            Length of time to store databases on the server.
      --njobs FIXIE_NJOBS   Number of jobs allowed in parallel on this server.
      --logfile FIXIE_LOGFILE
                            Path to the fixie logfile.
      --sims-dir FIXIE_SIMS_DIR
                            Path to fixie simulations directory, where simulation
                            objects are stored.
      --paths-dir FIXIE_PATHS_DIR
                            Path to fixie paths directory, where database path
                            metadata is stored.
      --data-url FIXIE_DATA_URL
                            Base URL for data service, default is an empty string
                            indicating service is provided locally (if available).
      --creds-url FIXIE_CREDS_URL
                            Base URL for creds service, default is an empty string
                            indicating service is provided locally (if available).
      --batch-url FIXIE_BATCH_URL
                            Base URL for batch service, default is an empty string
                            indicating service is provided locally (if available).
      --creds-dir FIXIE_CREDS_DIR
                            Path to fixie credentials directory
      --completed-jobs-dir FIXIE_COMPLETED_JOBS_DIR
                            Path to fixie completed jobs directory, must be
                            distinct from other status directories
      --failed-jobs-dir FIXIE_FAILED_JOBS_DIR
                            Path to fixie failed jobs directory, must be distinct
                            from other status directories
      --canceled-jobs-dir FIXIE_CANCELED_JOBS_DIR
                            Path to fixie canceled jobs directory, must be
                            distinct from other status directories
      --queued-jobs-dir FIXIE_QUEUED_JOBS_DIR
                            Path to fixie queued jobs directory, must be distinct
                            from other status directories
      --running-jobs-dir FIXIE_RUNNING_JOBS_DIR
                            Path to fixie running jobs directory, must be distinct
                            from other status directories
