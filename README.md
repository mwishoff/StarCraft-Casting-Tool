# StarCraft Casting Tool
![preview](https://user-images.githubusercontent.com/26044736/29332466-6899cd7e-8200-11e7-87de-f82b808b5413.png)


## General Information

StarCraft Casting Tool (SCC-Tool) is a Python 3.6 script that can load all relevant data of Stracraft 2 Team League Match from either [Alpha SC2 Teamleague](http://alpha.tl/) or [RSTL](http://hdgame.net/en/tournaments/list/tournament/rstl-12/) and convert it such that the information can be readily included for streaming, e.g., in OBS-Studio or X-Split. Moreover, the tool generates corresponding map icons for presentation on your stream, including the map, the players, their races, and the score (if played). Additionally, the title of your Twitch stream and your Nightbot chat commands can be updated accordingly by a single click. Furthermore, the tool can automatically dectect the score by monitoring your SC2-Client. On Windows the tool can automatically set and toogle the score in your SC2-Observer UI and toggle the production tab at the start of the game.

This tool should run on any operating system that supports Python, e.g., Windows, MacOS, and Linux. Yet, the interaction with the SC2-Observer-UI is currently only supported on Windows.  

## Installation

[Download](https://github.com/teampheenix/StarCraft-Casting-Tool/archive/master.zip) and exctract StarCraft Casting Tool, download the latest version of Python 3.6 at https://www.python.org/downloads. This tool requires the additional Python Packages *PyQt5*, *requests*, *configparser*, *flask* and on Windows additonally *pypiwin32*. To install these packages execute the script `installPackages.py` once or do it manually. Execute `StarCraftCastingTool.pyw` to start the SCC-Tool.

## Instructions for Use

Execute `StarCraftCastingTool.pyw` to start the SCC-Tool. Enter the Match-URL of an AlphaTL or RSTL match, e.g., "http://alpha.tl/match/2392". Press *Load Data from URL* and edit the data if necessary. The sliders control the score of each map. Press "Update OBS Data" or alter the score to update the data for streaming, which can be found in the directory `OBS_data` and can be included into OBS via *Text read from local file*. If you want to include the team logos and the matchbanner, it is recommended to include them as *browser source from local file* via the html files given in the directory `OBS_html` *(Banner: 1200x740px, Logos: 300x300px)*. The map icons can be found in the directory `OBS_mapicons` and have to be included via *browser source from local file* as well. There are two type of icons: box icons in `OBS_mapicons/icons_box` and landscape icons in `OBS_mapicons/icons_landscape`. One can either include each map icon separatly *(box size: 280x270px, landscape size: 750x75px)* and arrange them freely or one can include them via the single html file `all_maps.html` *(the choosen dimension of the browser source determines the arrangement of the icons)*. 

To update your [Twitch](https://www.twitch.tv/) title or [NightBot](https://nightbot.tv/) command via click on *Update Twitch Title* or *Update NightBot* you have to set your Twitch *Channel* and/or generate an corresponding access token. This can be done via *Settings: API-Integration*. Note that you can also change the title of twitch channels that do not belong to the user you have generated the access token with as long as this user is registered as an editor of corresponding channel.

The top slider is to select *your* team. Once selected the border of the map icons turn green or red depending on the result. To select your team by default you can set the parameter *myteams* in `config.ini` to a list of your team names separated by commas, e.g., `myteams = MiXed Minds, team pheeniX`. Similiarly you can enter your players' nicknames separated by commas into parameter *commonplayers* for autocompletion.

The automatic detection of the score via the SC2-Client-API does only work if you either play or observe a complete game (game length > 60 seconds) with a pair of players that were specified on one of the maps. 

## Customization

Some basic options for customization can be found in `config.ini`. You have to run SCC-Tool once to generate the `config.ini` file. For additional customization of the map icons you can alter the `/OBS_mapicons/src/map.css` file, e.g., try to replace `map.css` with `map_alternative.css`.

## Help & Contribution

If you need help, have bugs to report, have suggestions to make, or want to contribute to this project go to *#dev* channel of the [Alpha SC2 Discord Server](https://discordapp.com/invite/yRWNYr) and/or message me on Discord: *pres.sure#5247*. In the case of a bug report please provide the log-files `src/scctool.log` and `src/installpackages.log`.

## Support

If you want to support this project, consider subscribing to https://www.twitch.tv/teampheenix.

