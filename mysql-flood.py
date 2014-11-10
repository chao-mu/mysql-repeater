#!/usr/bin/env python

import argparse
import sys
import time

import MySQLdb

def main():
  arg_parser = argparse.ArgumentParser(
    description="Open simultaneous connections to MySQL and optionally execute a payload."
  )

  arg_parser.add_argument(
    "host",
    help="MySQL server"
  )
  arg_parser.add_argument(
    "--port",
    help="the port MySQL is listening on",
    type=int,
    default=3306
  )
  arg_parser.add_argument(
    "--max",
    help="max connections to attempt",
    type=int,
    # default max_connections is 151 and mysqld allows that + 1
    default=153
  )
  arg_parser.add_argument(
    "--user",
    help="user name to log in with",
    required=True
  )
  arg_parser.add_argument(
    "--password",
    help="password to log in with",
    required=True
  )
  arg_parser.add_argument(
    "--payload",
    help="SQL statement to execute immediately after connection",
    default="select 1"
  )
  arg_parser.add_argument(
    "--database",
    help="default database to use"
  )
  arg_parser.add_argument(
    "--skip-errors",
    help="Continue despite errors",
    action="store_true",
    default=False
  )
  arg_parser.add_argument(
    "--connection-delay",
    help="miliseconds to wait between connections.",
    default=0,
    type=int
  )
  arg_parser.add_argument(
    "--unique-errors",
    help="only report an error message/code combination once",
    action="store_true",
    default=False
  )
  arg_parser.add_argument(
    "--loop",
    help="after max is reached, start closing and reopening",
    action="store_true",
    default=False
  )
  arg_parser.add_argument(
    "--quiet",
    help="only print errors",
    action="store_true",
    default=False
  )

  args = arg_parser.parse_args()

  logger = FloodLogger(args.unique_errors, args.quiet)

  loop_count = 0
  while args.loop or loop_count == 0:
    loop_count += 1

    if args.loop:
      logger.log_status("Iteration #{}".format(loop_count))

    # Connect (connections will close if they get garbage collected)
    logger.log_status("Connecting {} times with {} milisecond delay.".format(
        args.max, args.connection_delay))
    connections = make_connections(args.host, args.user, args.password,
        args.max, args.skip_errors, args.connection_delay, logger)
    logger.log_status("Connections made: {} out of {}.".format(len(connections), args.max))

    if len(connections) == 0:
      logger.log_status("No connections made: nothing left to do.")
      continue

    # Execute payload
    logger.log_status("Executing payloads.")
    payloads_succeeded = execute_payload(connections, args.payload,
      args.skip_errors, logger)
    logger.log_status("Payloads succeeded: {} out of {}.".format(
        payloads_succeeded, len(connections)))

    # Close connection
    logger.log_status("Closing connections.")
    connections_closed = close_connections(connections, args.skip_errors, logger)
    logger.log_status("Connections closed: {} out of {}.".format(
       connections_closed, len(connections)))

def close_connections(connections, skip_errors, logger):
  connections_closed = 0
  for connection_i, connection in enumerate(connections):
    try:
      connection.close()
    except MySQLdb.OperationalError as e:
      logger.log_database_error("closing connection", connection_i + 1, e)

      if not skip_errors:
        sys.exit(1)

      continue

    connections_closed += 1

  return connections_closed

def make_connections(host, user, password, max_conns, skip_errors, connection_delay, logger):
  connections = []
  last_connect_s = None
  connection_delay_s = connection_delay / float(1000)

  for connection_i in range(max_conns):
    now_s = time.time()
    if last_connect_s is not None and connection_delay_s != 0 and \
        now_s - last_connect_s < connection_delay_s:
      time.sleep(connection_delay_s - (now_s - last_connect_s))
    try:
      connection = MySQLdb.connect(
        host=host,
        user=user,
        passwd=password
      )
      last_connect_s = time.time()
    except MySQLdb.OperationalError as e:
      logger.log_database_error("connecting", connection_i + 1, e)

      if not skip_errors:
        sys.exit(1)

      continue

    connections.append(connection)

  return connections

def execute_payload(connections, payload, skip_errors, logger):
  payloads_succeeded = 0
  for connection_i, connection in enumerate(connections):
    try:
      execute_sql(connection, payload);
    except (MySQLdb.OperationalError, MySQLdb.ProgrammingError) as e:
      logger.log_database_error("executing payload", connection_i + 1, e)

      if not skip_errors:
        sys.exit(1)

      continue

    payloads_succeeded += 1

  return payloads_succeeded

def execute_sql(connection, payload):
  cursor = connection.cursor()
  cursor.execute(payload)
  result = cursor.fetchall()
  cursor.close()

  return result

class FloodLogger(object):

  def __init__(self, suppress_duplicate_errors, quiet):
    self.error_counts = {}
    self.suppress_duplicate_errors = suppress_duplicate_errors
    self.quiet = quiet

  def log_status(self, msg):
    if self.quiet:
      return

    print("+ {}".format(msg))

  def log_database_error(self, context, connection_number, error):
    error_code = error[0]
    error_msg = error[1]

    error_count = self.error_counts.get((error_code, error_msg), 0) + 1
    self.error_counts[(error_code, error_msg)] = error_count

    if self.suppress_duplicate_errors and error_count > 1:
      return

    msg = "- Error code {} encountered when {} for connection #{}".format(
        error_code, context, connection_number)

    if self.suppress_duplicate_errors:
      msg += " (further errors of this kind will be suppressed)"

    msg += ": {}\n".format(error_msg)

    sys.stderr.write(msg)

if __name__ == "__main__":
  main()
