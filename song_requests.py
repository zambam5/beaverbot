import time, logging, random, json, requests, socket, re
import cfgzam as cfg
import spotipy
import spotipy.util as util
from irctools import chat


logger = logging.getLogger("__main__." + __name__)


def extract_link(message):
    match = re.search(r"(?P<url>open.spotify.com[^\s]+)", message)
    if match is not None:
        return match.group("url")
    else:
        return None


user = cfg.SPOTIFY_USER
playlist = cfg.SPOTIFY_PLAYLIST
CACHE = ".spotipyoauthcache"

# token = util.prompt_for_user_token(user, scope='playlist-modify-private playlist-modify-public',
#        client_id = cfg.SPOTIFY_ID, client_secret = cfg.SPOTIFY_SECRET,
#        redirect_uri=cfg.SPOTIFY_REDIRECT, cache_path=CACHE)

oauth = spotipy.oauth2.SpotifyOAuth(
    cfg.SPOTIFY_ID,
    cfg.SPOTIFY_SECRET,
    cfg.SPOTIFY_REDIRECT,
    scope="playlist-modify-public playlist-modify-private",
    cache_path=CACHE,
)

token = oauth.get_cached_token()
if token:
    sp = spotipy.Spotify(auth=token["access_token"])
else:
    print("Can't get token for ", user)

screwups = dict()


def song_requests(sock, message, url):
    global user, playlist, sp, token, oauth, screwups
    expired = spotipy.oauth2.is_token_expired(token)
    if expired:
        token = oauth.refresh_access_token(token["refresh_token"])
        sp = spotipy.Spotify(auth=token["access_token"])
        logger.info("token refreshed?")
    name = message["display-name"]
    m = message["message"]
    song = extract_link(m)
    if song == None and "spotify.link" in m:
        screwups[name] = (True, time.time())
        reply = f'{name}, I am unable to process links from spotify.link. To get a link I can process, when you go to share the song, open "More" and select either "Copy" or "Save URL". In the next 5 minutes, if you use !requeue with a new link you can try again.'
        return chat(
            sock,
            reply,
            cfg.CHAN,
        )
    elif song == None:
        screwups[name] = (True, time.time())
        return chat(
            sock,
            "{}, be sure your link is for open.spotify.com In the next 5 minutes, if you use !requeue with a new link you can try again.".format(
                name
            ),
            cfg.CHAN,
        )
    elif "track" not in song:
        screwups[name] = (True, time.time())
        return chat(
            sock,
            "{}, you have to link to a Spotify song for song requests. In the next 5 minutes, if you use !requeue with a new link you can try again.".format(
                name
            ),
            cfg.CHAN,
        )
    else:
        songl = [song]
        try:
            track1 = sp.track(song)
        except spotipy.client.SpotifyException:
            screwups[name] = (True, time.time())
            return chat(
                sock,
                "{}, that returned an error. In the next 5 minutes, if you use !requeue with a new link you can try again.".format(
                    name
                ),
                cfg.CHAN,
            )
        track = track1["id"]
        features = sp.audio_features(songl)[0]
        length = features["duration_ms"]
        tracks = sp.playlist_tracks(playlist)["items"]
        """if 'US' not in track1['available_markets']:
            chat(sock, "{}, sorry that song is not available in the US".format(name), cfg.CHAN)
            return"""
        if length > 360000:
            screwups[name] = (True, time.time())
            return chat(
                sock,
                "{}, we have a 6 minute limit on songs. In the next 5 minutes, if you use !requeue with a new song you can try again.".format(
                    name
                ),
                cfg.CHAN,
            )
        elif len(tracks) < 1:
            sp.user_playlist_add_tracks(user, playlist, songl, position=None)
            screwups[name] = (False, time.time())
            return chat(sock, "{}, song added to playlist".format(name), cfg.CHAN)
        else:
            for item in tracks[-11:]:
                print("here")
                check = item["track"]["id"]
                if track == check:
                    duplicate = True
                else:
                    duplicate = False
            if duplicate:
                screwups[name] = (True, time.time())
                return chat(
                    sock,
                    "{}, sorry that song is already in queue! In the next 5 minutes, if you use !requeue with a new song you can try again.".format(
                        name
                    ),
                    cfg.CHAN,
                )
            else:
                sp.user_playlist_add_tracks(user, playlist, songl, position=None)
                screwups[name] = (False, time.time())
                return chat(sock, "{} song added to playlist".format(name), cfg.CHAN)


def now_playing(sock, m):
    global playlist, sp, token, oauth
    expired = spotipy.oauth2.is_token_expired(token)
    if expired:
        token = oauth.refresh_access_token(token["refresh_token"])
        sp = spotipy.Spotify(auth=token["access_token"])
        logger.info("token refreshed?")
    data = sp.current_user_playing_track()
    if data == None:
        message = "/me The song is unknown, just like our futures FeelsBadMan"
        return chat(sock, message, cfg.CHAN)
    name = data["item"]["name"]
    artists = data["item"]["artists"]
    message = name + " by "
    if len(artists) == 1:
        message += artists[0]["name"]
    else:
        combined = ""
        for artist in artists:
            combined += artist["name"] + " & "
        message += combined[:-3]
    return chat(sock, "/me " + message, cfg.CHAN)


def clear_playlist(sock, message):
    global sp, token, oauth, user, playlist
    expired = spotipy.oauth2.is_token_expired(token)
    if expired:
        token = oauth.refresh_access_token(token["refresh_token"])
        sp = spotipy.Spotify(auth=token["access_token"])
        logger.info("token refreshed?")
    if message["mod"] == "1" or "broadcaster" in message["badges"]:
        tracks = sp.playlist_tracks(playlist)["items"]
        track_list = []
        for item in tracks:
            try:
                track_list.append(
                    item["external_urls"]["external_urls"]["linked_from"]["uri"]
                )
            except KeyError:
                track_list.append(item["track"]["id"])
        response = sp.user_playlist_remove_all_occurrences_of_tracks(
            user, playlist, track_list
        )
        logger.info("playlist cleared")
        return chat(sock, "Playlist cleared", cfg.CHAN)


def queue_length(sock, message):
    global sp, token, oauth, user, playlist
    expired = spotipy.oauth2.is_token_expired(token)
    if expired:
        token = oauth.refresh_access_token(token["refresh_token"])
        sp = spotipy.Spotify(auth=token["access_token"])
        logger.info("token refreshed?")
    tracks = len(sp.playlist_tracks(playlist)["items"])
    return chat(sock, "There are {} songs in queue".format(tracks), cfg.CHAN)


def requeue(sock, message):
    name = message["display-name"]
    if name in screwups.keys():
        if screwups[name][0] and time.time() - screwups[name][1] <= 300:
            song_requests(sock, message, cfg.URL)
        elif time.time() - screwups[name][1] > 300:
            del screwups[name]
            return chat(
                sock, "{}, sorry it's been more than 5 minutes".format(name), cfg.CHAN
            )


def mod_queue(sock, message):
    mod = int(message["mod"])
    if mod:
        song_requests(sock, message, cfg.URL)
