# Bugs to be handled later

### Invalid dates due to bad breaks
Sometimes the hyphen between the date and the rest is not surrounded by spaces,
and sometimes it doesn't exist.

The dates should be parsed with a regex for the year.