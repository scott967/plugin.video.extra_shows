# Copyright (C) 2023, Roman V. M.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
Example video plugin that is compatible with Kodi 20.x "Nexus" and above
"""

from __future__ import annotations

import re
import sys
import urllib.parse
from pathlib import Path

import xbmc
import xbmcgui
import xbmcplugin
from xbmcaddon import Addon
from xbmcvfs import translatePath
from resources.Lib import xmltodict

SHOW_PATH = Path('C:/test tvshow')
# Get the plugin url in plugin:// notation.
URL = sys.argv[0]
# Get a plugin handle as an integer number.
HANDLE = int(sys.argv[1])
# Get addon base path
ADDON_PATH = Path(translatePath(Addon().getAddonInfo('path')))
ADDON_NAME = Addon().getAddonInfo('name')
VIDEO_FORMATS = ['.mkv', '.mp4', '.avi', '.wtv']

# Public domain movies are from https://publicdomainmovie.net
# Here we use a hardcoded list of movies simply for demonstrating purposes
# In a "real life" plugin you will need to get info and links to video files/streams
# from some website or online service.

def logit(msg:str):
    """utility Kodi logging

    Args:
        msg (str): message to log
    """
    xbmc.log(f'{ADDON_NAME}: {msg}', xbmc.LOGDEBUG)

# parsers to get tvshow and episode nfo data

def get_matching_video(nfo_file:Path) -> Path:
    """checks for video file matching episode nfo
    using formats from VIDEO_FORMATS

    Args:
        nfo_file (Path): the episode nfo file to match

    Returns:
        Path: the matching video file
    """
    for vformat in VIDEO_FORMATS:
        if nfo_file.with_suffix(vformat).exists():
            return nfo_file.with_suffix(vformat)
    return None

def parse_nfo(nfo_file:Path) -> dict:
    """gets contents of Kodi nfo file as dict

    Args:
        nfo_file (Path): path/filename of nfo file

    Returns:
        dict: contents of nfo file as dict
    """
    nfo_details = xmltodict.parse(nfo_file.read_text(encoding='utf-8'))
    logit(f'parse_nfo  nfo details {nfo_details}')
    return nfo_details

def parse_episode_name(filename:str) -> dict:
    """gets season and episode ids from episode nfo file name

    Args:
        filename (str): the filename to parse

    Returns:
        dict: the episode as {'season': season_int, 'episode':episode_int}
    """
    #logit(f'parse_episode_name from {filename}')
    episode = {}
    season_no = re.search(r'[sS](\d+)', filename)
    #logit(f'parse_episode_name season match {season_no}')
    episode_no = re.search(r'[eE](\d+)', filename)
    #logit(f'parse_episode_name episode match {episode_no}')
    if season_no and episode_no:
        episode['season'] = season_no.group(1)
        episode['episode'] = episode_no.group(1)
    #logit(f'parse_episode_name episode S/E is {episode}')
    return episode

def get_tvshow_nfo(show:Path) -> dict:
    """finds a tvshow.nfo file in folder and returns content

    Args:
        show (Path): folder containing tv show

    Returns:
        dict: the tvshow.nfo as dict
    """
    for show_file in show.iterdir():
        if show_file.name == 'tvshow.nfo':
            test_parse = parse_nfo(show_file)
            #logit(f'get_tvshow_nfo results {test_parse}')
            return test_parse

def get_episode_nfo(episodes_dir:Path) -> list[dict]:
    """finds a set of episode.nfo files and returns content

    Args:
        episodes (Path): folder containing episodes

    Returns:
        list[dict]: a list of episodes -- each episode is a dict
    """
    logit(f'get_episode_nfo from {episodes_dir}')
    episode_list = []
    for episode_file in episodes_dir.iterdir():
        #logit(f'get_episode_nfo file is {episode_file}')
        if episode_file.suffix == '.nfo':
            logit(f'get_episode_nfo file is {episode_file.stem}')
            episode = parse_episode_name(episode_file.stem)
            if episode:
                video = get_matching_video(episode_file)
                if video:
                    episode['url'] = video
                    episode['details'] = parse_nfo(episode_file)
                    episode_list.append(episode)
    logit(f'get_episode_info episode list len {len(episode_list)}')
    return episode_list

def add_show_data(infoTag:xbmc.InfoTagVideo, show_info:dict) -> xbmc.InfoTagVideo:
    """adds data from tvshow nfo to the show's info tag

    Args:
        infoTag (xbmc.InfoTagVideo): the videoinfotag for the show
        show_info (dict): the show metadata from the nfo
    Returns:
        (xbmc:InfoTagVieo): the updated videoinfotag
    """
    infoTag.setMediaType('tvshow')
    infoTag.setTitle(show_info.get('title', ''))
    infoTag.setGenres(show_info.get('genre', []))
    infoTag.setPlot(show_info.get('plot', ''))
    infoTag.setPremiered(show_info.get('premiered', ''))
    return infoTag

def add_episode_data(infoTag:xbmc.InfoTagVideo, episode_info:dict) -> xbmc.InfoTagVideo:
    """adds data from episode nfo to the episode's info tag

    Args:
        infoTag (xbmc.InfoTagVideo): the videoinfotag for the episode
        episode_info (dict): the episode metadata from the nfo
    Returns:
        (xbmc:InfoTagVieo): the updated videoinfotag
    """
    logit(f'add_episode_data from {episode_info}')
    infoTag.setMediaType('episode')
    infoTag.setTitle(episode_info.get('title', ''))
    infoTag.setPlot(episode_info.get('plot', ''))
    if episode_info.get('year'):
        infoTag.setYear(int(episode_info['year']))
    infoTag.setFirstAired(episode_info.get('aired'))
    return infoTag

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    logit(f'get_url {URL}?{urllib.parse.urlencode(kwargs, quote_via=urllib.parse.quote)}')
    return f'{URL}?{urllib.parse.urlencode(kwargs, quote_via=urllib.parse.quote)}'

def get_art(art_type:str, art_dir:Path) -> Path:
    """finds local art for an artype

    Args:
        art_type (str): the arttype eg poster/fanart
        art_dir (Path): tv show folder with local art

    Returns:
        Path: path/filename of image file
    """
    for file in art_dir.iterdir():
        if file.stem == art_type and (file.suffix == '.jpg' or '.png'):
            return file

def get_shows() ->list:
    """
    Get the list of videofiles/streams.

    Here you can insert some code that retrieves
    the list of video streams in the given section from some site or API.

    :param genre_index: genre index
    :type genre_index: int
    :return: the list of tv shows
    :rtype: list
    """
    shows = []
    for show in SHOW_PATH.iterdir():
        if show.is_dir():
            logit(f'get_shows get info for {show}')
            show_data = get_tvshow_nfo(show)
            show_data['art'] = {}
            for art_type in ('banner', 'fanart', 'poster'):
                art = get_art(art_type, show)
                if art:
                    show_data['art'][art_type] = art
            show_data['dir'] = show
            shows.append(show_data)
    logit(f'get_shows len is  {len(shows)}')
    return shows

def get_episodes(show_dir:Path) ->list:
    """
    Get the list of videofiles/streams.

    Here you can insert some code that retrieves
    the list of video streams in the given section from some site or API.

    :param genre_index: genre index
    :type genre_index: int
    :return: the list of tv shows
    :rtype: list
    """
    episodes = get_episode_nfo(show_dir)
    #logit(f'get_episodes {episodes}')
    return episodes

def list_shows():
    """creates a Kodi container of tv show listitems.  The url gets
    Kodi container of episodes 
    """
        # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(HANDLE, 'TV Shows ')
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(HANDLE, 'tvshows')
    # Get movie genres
    shows = get_shows()
    # Iterate through genres
    for show_info in shows:
        # Create a list item with a text label.
        list_item = xbmcgui.ListItem(label=show_info['tvshow']['title'])
        # Set images for the list item.
        list_item.setArt({'poster': str(show_info['art']['poster']), 'fanart': str(show_info['art']['fanart'])})
        # Set additional info for the list item using its InfoTag.
        # InfoTag allows to set various information for an item.
        # For available properties and methods see the following link:
        # https://codedocs.xyz/xbmc/xbmc/classXBMCAddon_1_1xbmc_1_1InfoTagVideo.html
        # 'mediatype' is needed for a skin to display info for this ListItem correctly.
        info_tag:xbmc.InfoTagVideo = list_item.getVideoInfoTag()
        add_show_data(info_tag, show_info['tvshow'])
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=listing&genre_index=0
        url = get_url(action='listing', show_dir=str(show_info['dir']), show_title=show_info['tvshow']['title'])
        # is_folder = True means that this item opens a sub-list of lower level items.
        is_folder = True
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    # Add sort methods for the virtual folder items
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(HANDLE)

def list_episodes(show_path:Path, show_title:str):
    """
    Create the list of playable videos in the Kodi interface.

    :param genre_index: the index of genre in the list of movie genres
    :type genre_index: int
    """
    logit(f'list_episodes for {show_path} and {show_title}')
    episodes = get_episodes(show_path)
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    xbmcplugin.setPluginCategory(HANDLE, show_title)
    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(HANDLE, 'episodes')
    # Get the list of videos in the category.
    for video in episodes:
        # Create a list item with a text label
        list_item = xbmcgui.ListItem(label=video['details']['episodedetails']['title'])
        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use only poster for simplicity's sake.
        # In a real-life plugin you may need to set multiple image types.
        #list_item.setArt({'poster': video['poster']})
        # Set additional info for the list item via InfoTag.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        info_tag:xbmc.InfoTagVideo = list_item.getVideoInfoTag()
        add_episode_data(info_tag, video['details']['episodedetails'])
        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')
        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=https%3A%2F%2Fia600702.us.archive.org%2F3%2Fitems%2Firon_mask%2Firon_mask_512kb.mp4
        url = get_url(action='play', video=video['url'])
        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False
        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    # Add sort methods for the virtual folder items
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(HANDLE)


def play_video(path):
    """
    Play a video by the provided path.

    :param path: Fully-qualified video URL
    :type path: str
    """
    # Create a playable item with a path to play.
    # offscreen=True means that the list item is not meant for displaying,
    # only to pass info to the Kodi player
    play_item = xbmcgui.ListItem(offscreen=True)
    play_item.setPath(path)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(urllib.parse.parse_qsl(paramstring))
    if params:
        logit(f'router params {params}')
    else:
        logit('router no params')
    # Check the parameters passed to the plugin
    if not params:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of tv shows
        list_shows()
    elif params['action'] == 'listing':
        # Display the list of episodes in a provided tv show.
        list_episodes(Path(params['show_dir']), params['show_title'])
    elif params['action'] == 'play':
        # Play a video from a provided URL.
        play_video(params['video'])
    else:
        # If the provided paramstring does not contain a supported action
        # we raise an exception. This helps to catch coding errors,
        # e.g. typos in action names.
        raise ValueError(f'Invalid paramstring: {paramstring}!')


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
