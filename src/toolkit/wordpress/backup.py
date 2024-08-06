import logging
import shutil
import subprocess
import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path


def configure_logging(debug: bool) -> None:
    """Configures the logging settings based on the debug flag."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

def backup_wordpress_dir(args: ArgumentParser, filename: str) -> None:
    """Run backup wordpress directory"""
    logger = logging.getLogger("backup_wordpress")
    logger.debug("Wordpress directory: %s", args.wp_dir)
    logger.debug("Backup file: %s", filename)
    shutil.make_archive(filename, "gztar", args.wp_dir)


def backup_database(args: ArgumentParser, filename: str) -> None:
    """Run backup wordpress database"""
    logger = logging.getLogger("backup_database")
    
    db_backup_cmd = [
        "mysqldump",
        "-u", args.username,
        f"-p{args.password}",
        "-h", args.host,
        args.database,
    ]
    try:
        with filename.open("w") as f:
            subprocess.run(db_backup_cmd, stdout=f, check=True)
        logger.debug("WordPress database backed up to '%s'", filename)
    except subprocess.CalledProcessError:
        raise

def backup(args: ArgumentParser):

    logger = logging.getLogger("backup")
    logger.info("Start backing up wordpress")

    backup_dir = Path(args.backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_file = Path(backup_dir, f"wordpress_files_{date_str}.tar.gz")
    backup_file_basename = backup_file.as_posix().split(".")[0]
    db_backup_file = Path(backup_dir, f"wordpress_db_{date_str}.sql")

    # Backup WordPress files
    backup_wordpress_dir(args, filename=backup_file_basename)

    # Backup WordPress database
    backup_database(args, db_backup_file)

    logger.info("Backup complete")
    logger.info("Wordpress backup: %s", backup_file)
    logger.info("Database backup: %s", db_backup_file)


def main() -> int:
    parser = ArgumentParser(prog="wp-backup")
    parser.add_argument("--database", help="Database name", required=True)
    parser.add_argument("--username", help="Database username", required=True)
    parser.add_argument("--password", help="Database password", required=True)
    parser.add_argument("--backup-dir", help="Backup directory", required=True)
    parser.add_argument("--wp-dir", help="Wordpres directory", default="/var/www/html")
    parser.add_argument("--host", help="Database host", default="localhost")
    parser.add_argument("--debug", help="Enable debug logs", action="store_true")

    parser.set_defaults(func=backup)

    args = parser.parse_args()
    configure_logging(args.debug)
    logger = logging.getLogger("main")
    logger.debug("Debug enabled")

    if hasattr(args, "func"):
        try:
            args.func(args)
        except Exception as e:
            logger.error("Error: %s", e)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
