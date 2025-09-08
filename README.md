# How to install

### Docker Compose
```yaml
services:
  qbit-cleaner:
    image: silentesc/qbit-cleaner:latest
    container_name: qbit-cleaner
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
      - TORRENTS_PATH=/data/path/to/torrents
      - MEDIA_PATH=/data/path/to/media
    volumes:
      - /path/to/config:/config
      - /path/to/data:/data
    restart: unless-stopped
```

### Create config.yaml in config folder for qbit-cleaner
```yaml
testing:
  # Testing a job without waiting for the interval
  # Scheduler will not be started after the test run
  job:

logging:
  # TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_level: DEBUG

notifications:
  # Keep empty to disable notifications
  discord_webhook_url:

qbittorrent:
  # Credentials
  host: localhost
  port: 8080
  username: admin
  password: adminadmin

  # Config
  protected_tag: protected

jobs:
  delete_orphaned:
    # Execute this job every x hours, 0 to disable
    interval_hours: 11
    # What happens when a orphaned file been found
    # test - everything works (including notifications) but nothing happens with the file
    # delete - file will be deleted
    action: test

  delete_forgotten:
    # Execute this job every x hours, 0 to disable
    interval_hours: 10
    # The minimum amount of days a torrent had to be seeding before getting deleted
    min_seeding_days: 20
    # The minimum amount of days the torrent has to be forgotten before getting deleted
    min_strike_days: 0
    # The minimum amount of strikes the torrent has to get before getting deleted
    required_strikes: 0
    # What happens when a forgotten torrent has been found
    # test - everything works (including notifications) but nothing happens with the torrent
    # stop - Torrent will be stopped
    # delete - Torrent + files will be deleted
    action: test

  delete_not_working_trackers:
    # Execute this job every x hours, 0 to disable
    interval_hours: 3
    # The minimum amount of days the trackers has to be not working before getting deleted
    # If the trackers work in the meantime, it resets the days counter
    min_strike_days: 7
    # The minimum amount of strikes the torrent has to get before getting deleted
    # If the trackers work in the meantime, it resets the strikes counter
    required_strikes: 10
    # What happens when a torrent without working trackers has been found and minimum criteria are met
    # test - everything works (including notifications) but nothing happens with the torrent
    # stop - Torrent will be stopped
    # delete - Torrent + files will be deleted
    action: test
```
