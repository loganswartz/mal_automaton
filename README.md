# mal_automaton
Automatic updating of your MAL via Plex webhooks.

![Build Status](https://github.com/loganswartz/mal_automaton/workflows/Lint%20&amp;%20Test/badge.svg)

## Todo
- [ ] Smarter series matching
- [x] TVDB objects
- [ ] Improve TVDB objects
- [ ] Flask webhook ingress
- [ ] Add more tests

## Purpose
MyAnimeList (MAL) is a website that tracks all the anime series that a person has watched, along with the specific episode, ratings, etc associated with that series. However, doing so manually can be a bit of a PITA when you are watching several shows in a single anime season, so I had the idea to automate updating my list by listening to the webhooks generated by Plex, and masquerading as the appropriate user.

## Usage
Currently, there is no webserver / HTTP endpoint functionality implemented in `mal_automaton`. Eventually I plan on adding that in via Flask, but currently you can process an arbitrary number of webhooks manually by running `mal_automaton` as a module and passing saved webhooks as command line arguments, like so:
```bash
$ python3 -m mal_automaton your-webhook-here.json your-2nd-webhook-here.json
```
Plex webhooks are JSON payloads, and you can use sites such as [webhook.site](https://webhook.site/) to easily listen for webhooks. Add the custom URL endpoint into Plex in the "Webhooks" section, and then start playing something in Plex and wait for the webhook to show up. You can then copy the payload of the request and save it as a `.json` file. At this point, that `.json` file can be read into `mal_automaton`, and it will attempt to match the episode specified in the webhook with an series + episode in MAL.

### `MAL` objects
`mal.py` contains definitions for the `MAL_Franchise`, `MAL_Series`, and `MAL_Episode` objects.
##### `MAL_Franchise`
```python
>>> from mal_automaton.mal import MAL_Franchise

# Create a franchise (*see the Terminology section of the README for more info)
>>> snk_franchise = MAL_Franchise(16498)       # created the same way as a MAL_Series, either by name or MAL ID
<MAL_Franchise: Shingeki no Kyojin>            # the franchise you create will be whatever "franchise" the supplied series is a part of.

# Get info on the franchise
>>> snk_franchise.series
[<MAL_Series: Shingeki no Kyojin [16498]>, <MAL_Series: Shingeki no Kyojin Season 2 [25777]>, <MAL_Series: Shingeki no Kyojin Season 3 [35760]>, <MAL_Series: Shingeki no Kyojin Season 3 Part 2 [38524]>, <MAL_Series: Shingeki no Kyojin The Final Season [40028]>]
>>> snk_franchise.title
'Shingeki no Kyojin'
>>> snk_franchise.absolute_episode(57)         # get an episode by absolute numbering
<MAL_Episode: That Day [8]>
>>> snk_franchise.release_run                  # get a tuple marking the beginning and end of the franchise
(datetime.datetime(2013, 4, 7, 0, 0, tzinfo=tzutc()), None)
```

##### `MAL_Series`
```python
>>> from mal_automaton.mal import MAL_Series

# Create a series
>>> snk = MAL_Series(16498)                    # using the MAL ID
>>> aot = MAL_Series(name='Attack on Titan')   # using a name
>>> snk
<MAL_Series: Shingeki no Kyojin [16498]>

# Get info on a series
>>> snk.title
'Shingeki no Kyojin'
>>> snk.airing                   # boolean, is currently airing?
False
>>> snk.id                       # return the MAL ID
16498
>>> snk.episodes                 # list of all the episodes in the series
[<MAL_Episode: To You Two Thousand Years Later [1]>, <MAL_Episode: That Day [2]>, <MAL_Episode: Shining Dimly in the Midst of Despair [3]>, <MAL_Episode: Night of the Disbanding [4]>, <MAL_Episode: First Battle [5]>, <MAL_Episode: The World She Saw [6]>, <MAL_Episode: The Small Blade [7]>, <MAL_Episode: Hearing the Heartbeat [8]>, <MAL_Episode: The Left Arm's Trace [9]>, <MAL_Episode: Answer [10]>, <MAL_Episode: Idol [11]>, <MAL_Episode: Wound [12]>, <MAL_Episode: Primordial Desire [13]>, <MAL_Episode: Can't Look Into His Eyes [14]>, <MAL_Episode: Special Operations Squad [15]>, <MAL_Episode: What To Do Now [16]>, <MAL_Episode: The Female Titan [17]>, <MAL_Episode: The Forest of Giant Trees [18]>, <MAL_Episode: Bite [19]>, <MAL_Episode: Erwin Smith [20]>, <MAL_Episode: Crushing Blow [21]>, <MAL_Episode: The Defeated [22]>, <MAL_Episode: Smile [23]>, <MAL_Episode: Mercy [24]>, <MAL_Episode: Wall [25]>]
>>> snk.release_season          # what anime season did the show release in?
'Spring 2013'
>>> snk.synonyms
['AoT']
>>> snk.title_en                # English title
'Attack on Titan'
>>> snk.title_jp                # Japanese title
'進撃の巨人'
>>> snk.type                    # Movie, TV Show, etc
<AnimeType.TV: 'TV'>

# Other features of MAL_Series
>>> snk = MAL_Series(16498)                    # using the MAL ID
>>> aot = MAL_Series(name='Attack on Titan')   # using a name
>>> snk is aot
True               # every unique series is a singleton, no matter how or when it is created
```

## How it works
(Let's use Attack on Titan S3E20, 'That Day' as an example)

To match an event to a series in MAL, we follow several steps:
1. Take the name of the show in the webhook (series name = 'Attack on Titan', according to Plex/TheTVDB)
2. Search for that name in MAL via Jikan, and take the first result (we get the series 'Shingeki no Kyojin', which is equivalent to _just_ the first season of 'Attack on Titan' on TheTVDB)
3. Assemble a `MAL_Franchise` object that contains all the related prequels and sequels of the series we found (the resulting `MAL_Franchise` object contains a list of 5 series: SnK, SnK S2, SnK S3 P1, SnK S3 P2, and SnK S4)
4. Look through every series in the franchise, and try to find an episode that aired within ~1 day of the advertised airdate in TheTVDB. (We find that episode 8 of 'Snk S3 P2' aired within 1 day of the episode we're looking for, according to TheTVDB)
5. If we don't find anything via airdates, then we fallback to looking for an exact matching title.

Thus, we end with finding that TheTVDB's `'Attack on Titan' S03E20` has a MAL equivalent of `'Shingeki no Kyojin Season 3 Part 2' E08`.

## Terminology
You may be thinking:
> Why don't you just take the show, season, and episode that Plex reports and use that directly to update my MAL?

However, Japan and the anime industry typically conceptualize shows in a different way than we do in America, so things don't map 1-to-1 from American content trackers like TheTVDB, and primarily Japanese ones like MAL. In the US we typically see a single show with several seasons, but in the anime industry, that same show is instead viewed as several separate "series" that come one after another. Typically this isn't too much of an issue as finding all the preceding and successive series isn't too hard since a single season in America perfectly correlates to a Japanese series.....except when it doesn't, like how Season 3 of Attack on Titan is actually 2 separate series on MAL due to having a midseason break. Hence, we have to be smarter about matching seasons to series because things just aren't consistent at all. Here's a table of how things _typically_ correlate:

TheTVDB | MAL | This project's `MAL` objects
--------|-----|-----------------------------
Show | Several different series | `MAL_Franchise`
Season | Series | `MAL_Series`
Episode | Episode | `MAL_Episode`

