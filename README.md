# TLS Report Reader

Analyzes STS-TLS reports on an IMAP server and either
- reports errors, or
- general statistics
to standard output or to a matrix room (if a homeserver is configured).

## Usage
```
tls-report-reader.py [-h] [--days N] [--stats] [-c CONFIG]

Analyze TLS reports.

optional arguments:
  -h, --help            show this help message and exit
  --days N              Number of days to summarize
  --stats               Print statistics, even if no errors have been reported.
  -c CONFIG, --config CONFIG
                        Location of the configuration file.
```

## Dependencies

- matrix-nio library 


## Setup
This setup uses crontab to call TLS report reader. The daily job parses STS TLS reports from the last 24 hours and reports errors only. The second job computes statistics based on reports received within the last seven days.

```crontab
# daily checkup for error
21 6	* * * 	robot 	/srv/tls-report-reader/tls-report-reader.py --config /srv/tls-report-reader/tls-report-reader.json

# weekly statistics
27 6	* * *	robot	/srv/tls-report-reader/tls-report-reader.py --config /srv/tls-report-reader/tls-report-reader.json --days 7 --stats
```
