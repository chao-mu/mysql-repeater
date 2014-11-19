About
======================

Debugging tool for connecting to a MySQL server repeatedly, executing something, closing the connections, and then repeating.

This is a super super raw hack whipped out in my free time to debug an issue, so I recommend against using it to diagnose production issues. It's posted here on the off-chance I'll want to come back and improve it.

Install
======================

This script requires MySQLdb, which is available via the mysql-python python package, installable with pip or easy_install. It has a number of dependencies and so it may be easier to install via your system's package manager (if available). Below shows it being installed on Ubuntu:

```
$ sudo apt-get install python-mysqldb
```

Usage
======================
```
usage: mysql-flood.py [-h] [--port PORT] [--max MAX] --user USER --password
                      PASSWORD [--payload PAYLOAD] [--database DATABASE]
                      [--skip-errors] [--connection-delay CONNECTION_DELAY]
                      [--unique-errors] [--loop] [--quiet]
                      host

Open connections to MySQL and then optionally execute a payload.

positional arguments:
  host                  MySQL server

optional arguments:
  -h, --help            show this help message and exit
  --port PORT           the port MySQL is listening on
  --max MAX             max connections to attempt
  --user USER           user name to log in with
  --password PASSWORD   password to log in with
  --payload PAYLOAD     SQL statement to execute immediately after connection
  --database DATABASE   default database to use
  --skip-errors         Continue despite errors
  --connection-delay CONNECTION_DELAY
                        miliseconds to wait between connections.
  --unique-errors       only report an error message/code combination once
  --loop                after max is reached, start closing and reopening
  --quiet               only print errors
```
