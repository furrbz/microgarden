# microgarden
Scripts to control an indoor garden with a raspberry pi and relays

A group of Python scripts to control via crontab on an RPi4. I used an EZO-HUM from Atlas Scientific, enabled by UART - meaning your RPi4 must have UART enable as well (some cmdline changes need to be made). The smaller scripts for lights active and deactivate a relay which the lights would be connected to. The Humidity and Temp controller scripts run every 5 minutes and if temp or humidity is too high, they active a relay for 4.5 minutes, after which they turn off before the next cycle. Each 5 minute interval the script also records the temp, humidity, datetime in a database. The data from the last 12 hours is communicated via email a few times per day in order to help keep an eye on things. Next steps would be to create some sort of on demand interface, whether with an API, or flask, or a Django site. 
