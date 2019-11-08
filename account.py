#!/usr/bin/env python3

#builtins
import logging

# 3rd party
import requests

# my modules
from mal_automaton.anime import AnimeList, WatchStatus
from mal_automaton.utils import retry


log = logging.getLogger(__name__)

class MAL_Account(object):
    """
    An MAL user account object, used to make changes to your list. This
    class provides a high-level, abstracted interface with MAL, allowing for
    actions such as correctly marking episodes as watched, etc. Inits a
    MAL_Session object and a Jikan object to interface with MAL. The
    MAL_Session object handles the raw MAL API transactions involved with
    making modifications to lists, and the Jikan object handles all the
    fetching of information from MAL.
    """
    def __init__(self, username, password = None):
        self.username = username
        self.password = password
        if password:
            self.user = MAL_Session(self.username, password)
        else:
            log.warning('No password given, modifications cannot be made to your list until you call add_password().')
        self.get_list()

    @retry(tries=3)
    def get_list(self):
        self.anime_list = AnimeList(self.username)

    def add_password(self, password):
        self.user = MAL_Session(self.username, password)

    def needs_auth(func):
        def wrapper(self, *args, **kwargs):
            if not self.user:
                raise Exception('You need to be authenticated to do this.')
            return func(*args, **kwargs)
        return wrapper

    @property
    def title_list(self):
        return [i.title for i in self.anime_list.entries.values()]

    @needs_auth
    def add_series(self, mal_id):
        return self.user.add_series(mal_id)

    @needs_auth
    def watch_episode(self, mal_id, episode):
        # if we aren't already watching the anime, add it and mark as watching
        if mal_id not in self.anime_list:
            return self.user.add_series(mal_id, status=WatchStatus.Watching, num_watched_episodes=episode)

        # else, get the current status of the anime in question
        anime = self.anime_list[mal_id]
        status = anime.status

        # did they watch a new episode according to their list?
        watched_new_episode = episode > status.watched_episodes

        if watched_new_episode:
            # update the local list
            status.watched_episodes = episode

            # if it was the last episode
            if episode >= anime.total_episodes:
                # mark as complete
                return self.user.edit_series(mal_id, WatchStatus.Completed, status.score, episode)
            else:
                # mark as watching and change episode
                return self.user.edit_series(mal_id, WatchStatus.Watching, status.score, episode)
        else:
            # return None if we don't update anything
            return None

    @needs_auth
    def remove_series(self, mal_id):
        return self.user.delete_series(mal_id)


class MAL_Session(object):
    """
    This class allows you to make raw API transactions with MAL, specifically
    ones that edit or change your list in some way. If you want to retrieve
    information from a list, use a Jikan() instance instead (Or if you want to
    do both, use the MAL_Account class, which utilizes instances of both Jikan
    and MAL_Session)
    """
    headers = {
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
    }

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.login()

    def login():
        mal_login = 'https://myanimelist.net/login.php'

        # grab the csrf_token
        prefetch = self.session.get(mal_login)
        csrf_regex = r"<meta name='csrf_token' content='(.*?)'>"
        match = re.search(csrf_regex, prefetch.text)
        if not match:
            raise Exception('No CSRF token found')
        self.csrf_token = match.groups(0)

        # actually log in
        resp = self.session.post(mal_login, headers=self.headers, data=self.login_data)
        return (resp.url == 'https://myanimelist.net')

    @property
    def login_data(self):
        data = {
            'user_name' : self.username,
            'password'  : self.password,
            'csrf'      : self.csrf_token,
            'cookie'    : '1',
            'sublogin'  : 'Login',
            'submit'    : '1',
        }
        return data

    def add_series(mal_id, status = WatchStatus.PlanToWatch, score = 0, watched_episodes = 0):
        url = 'https://myanimelist.net/ownlist/anime/add.json'
        data = {
            'csrf'      : self.csrf_token,
            'anime_id'  : mal_id,
            'status'    : int(status),
            'score'     : score,
            'num_watched_episodes': watched_episodes
        }

        resp = self.session.post(url, data=data, headers=self.headers)
        return resp.ok

    def edit_series(mal_id, status = WatchStatus.Watching, score = 0, watched_episodes = 0):
        url = 'https://myanimelist.net/ownlist/anime/edit.json'
        data = {
            'csrf'      : self.csrf_token,
            'anime_id'  : mal_id,
            'status'    : int(status),
            'score'     : score,
            'num_watched_episodes': watched_episodes
        }

        resp = self.session.post(url, data=data, headers=self.headers)
        return resp.ok

    def delete_series(mal_id):
        url = f'https://myanimelist.net/ownlist/anime/{mal_id}/delete'
        data = {'csrf': self.csrf_token}

        resp = self.session.post(url, data=data, headers=self.headers)
        return resp.ok

