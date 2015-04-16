#!/usr/bin/env python
import os
import sys
import json
from mutagen.mp4 import MP4
from mutagen.id3 import ID3
from mutagen.id3 import ID3NoHeaderError
from gmusicapi import Mobileclient


EMAIL = "YOUR-EMAIL-HERE"
PASSWORD = "YOUR-PASSWORD-HERE"


def remove_dups(tracks):
    track_set = []
    for track in tracks:
        current = {'title': track['title'].lower(), 'artist': track['artist'].lower(), 'album': track['album'].lower()}
        if not current in track_set:
            track_set.append(current)
    return track_set


def find_in_lib(path, tracks):
    exists, missing = 0, 0
    no_data, not_audio, paths = [], [], []
    for root, dirs, files in os.walk(path):
        print "%d files in %s folder" % (len(files), root)
        for song in files:
            # I only had mp3 and m4a files in my lib, expand this check if needed.
            if ".mp3" in song.lower() or ".m4a" in song.lower():
                data = get_metadata(os.path.join(root, song))
                if data:
                    if data in tracks:
                        print("EXISTS: %s\n" % song)
                        exists += 1
                    else:
                        print("DOESN'T EXIST: %s\n" % song)
                        paths.append(os.path.join(root, song))
                        missing += 1
                else:
                    print("NO METADATA COULD BE EXTRACTED: %s\n" % song)
                    no_data.append(os.path.join(root, song))
            else:
                not_audio.append(song)

    print("THE FOLLOWING ARE NOT AUDIO FILES:")
    print(json.dumps(not_audio))
    print("\n")
    print("FAILED TO EXTRACT METADATA FROM THE FOLLOWING:")
    print(json.dumps(no_data))
    print("\n")
    print("PATHS OF MISSING SONGS:")
    print(json.dumps(paths))
    print("\n")
    print("\n")
    print("TOTAL MISSING: %s" % missing)
    print("TOTAL EXISTS: %s" % exists)
    return no_data + paths


def get_metadata(song):
    try:
        if ".mp3" in song.lower():
            tags = ID3(song)
            try:
                return {"title": tags["TIT2"].text[0].lower(), "artist": tags["TPE1"].text[0].lower(), "album": tags["TALB"].text[0].lower()}
            except KeyError:
                return {"title": tags["TIT2"].text[0].lower(), "artist": tags["TPE2"].text[0].lower(), "album": tags["TALB"].text[0].lower()}
        else:
            tags = MP4(song)
            return {"title": tags["\xa9nam"][0].lower(), "artist": tags["\xa9ART"][0].lower(), "album": tags["\xa9alb"][0].lower()}
    except KeyError:
        print("key not found")
        return False
    except ID3NoHeaderError:
        print("%s has no id3 tags" % song)
        return False


def main(path):
    api = Mobileclient()
    logged_in = api.login(EMAIL, PASSWORD)

    if logged_in:
        print("Succesfully logged in, retrieving all songs and running check...")
        all_songs = api.get_all_songs()
        tracks = remove_dups(all_songs)
        results = find_in_lib(path, tracks)
        print("saving file to %s" % os.path.join(os.getcwd(), "output.json"))
        with open("output.json", "w+") as f:
            f.write(json.dumps(results))
            f.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("USAGE:")
        print("./%s path_to_music_folder\n" % sys.argv[0])
        print("Will try to match songs from given directory in your google music library")
        print("Once finished, an array of the paths of songs that don't exist/failed to be compared will be saved as 'output.json'")
        sys.exit(0)
    else:
        main(sys.argv[1])
