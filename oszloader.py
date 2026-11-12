from pathlib       import Path
from bitarray      import bitarray
from bitarray.util import int2ba
from dataclasses   import dataclass
from enum          import IntEnum, auto
import zipfile

@dataclass
class Beatmapset:
    title: str
    artist: str
    filename: str
    versions: list[str]

@dataclass
class HitObject:
    timestamp: float
    end_time:  float
    key:       int
    pressed:   bool
    hitsounds: bitarray

class Mode(IntEnum):
    NONE         = 0
    GENERAL      = auto()
    EDITOR       = auto()
    METADATA     = auto()
    DIFFICULTY   = auto()
    EVENTS       = auto()
    TIMINGPOINTS = auto()
    HITOBJECTS   = auto()
    COLOURS      = auto()

MODES = {
    "[General]"      : Mode.GENERAL     ,
    "[Editor]"       : Mode.EDITOR      ,
    "[Metadata]"     : Mode.METADATA    ,
    "[Difficulty]"   : Mode.DIFFICULTY  ,
    "[Events]"       : Mode.EVENTS      ,
    "[TimingPoints]" : Mode.TIMINGPOINTS,
    "[HitObjects]"   : Mode.HITOBJECTS  ,
    "[Colours]"      : Mode.COLOURS     ,
}

def directory_preview(directory_name):
    res: list[Beatmapset] = []
    for archive in Path(directory_name).glob("*.osz"):
        beatmapset_filename = archive.name
        beatmaps = list(zipfile.Path(directory_name + "/" + beatmapset_filename).glob("*.osu"))
        sample_beatmap_filename = beatmaps[0].name
        title  = loadSpecific(directory_name, beatmapset_filename, sample_beatmap_filename, "Title")
        artist = loadSpecific(directory_name, beatmapset_filename, sample_beatmap_filename, "Artist")
        beatmapset = Beatmapset(title, artist, beatmapset_filename, [])
        beatmapset_id = loadSpecific(directory_name, beatmapset_filename, sample_beatmap_filename, "BeatmapSetID")

        for beatmap in beatmaps:
            beatmap_filename = beatmap.name
            difficulty_level = float(loadSpecific(directory_name, beatmapset_filename, beatmap_filename, "OverallDifficulty"))
            difficulty_name  = loadSpecific(directory_name, beatmapset_filename, beatmap_filename, "Version")
            beatmap_id       = loadSpecific(directory_name, beatmapset_filename, beatmap_filename, "BeatmapID")
            beatmapset.versions.append((difficulty_name, difficulty_level, beatmap_filename, beatmapset_id + beatmap_id))

        beatmapset.versions.sort(key=lambda xs: xs[1])
        res.append(beatmapset)
    return res

def loadSpecific(directory_name, beatmapset_name, beatmap_name, target_key):
    with zipfile.ZipFile(directory_name + "/" + beatmapset_name) as zf:
        with zf.open(beatmap_name, "r") as f:
            for line in f:
                line = line.strip().decode()

                if line == "" or line.startswith("//") or line.startswith("["):
                    continue
    
                split_result = line.split(":")
                if len(split_result) == 2:
                    key, val = split_result
                    if key == target_key:
                        return val
        return None

def load(directory_name, beatmapset_name, beatmap_name):
    hit_objects = []
    bpm = 0.0

    with zipfile.ZipFile(directory_name + "/" + beatmapset_name) as zf:
        with zf.open(beatmap_name, "r") as f:
            properties = {}
    
            mode = Mode.NONE
    
            for line in f:
                line = line.strip().decode()

                if line == "" or line.startswith("//"):
                    continue
    
                if line.startswith("["):
                    mode = MODES[line]
                    continue
    
                match mode:
                    case Mode.NONE:
                        pass
                    case Mode.EVENTS:
                        pass
                    case Mode.TIMINGPOINTS:
                        xs = line.split(",")
                        uninherited = bool(int(xs[-2]))
                        if uninherited:
                            bpm = 60_000 / float(xs[1])
                    case Mode.HITOBJECTS:
                        xs = line.split(",")
                        x, y, time, type_, hitsounds = map(int, xs[:5])
    
                        xs = xs[-1].split(":")[:-1]
                        end_time, *hit_sample = map(int, xs)
    
                        key = x * int(properties["CircleSize"]) // 512
                        hit_objects.append(
                            HitObject(
                                time / 1000,
                                max((end_time - time) / 1000 , 0.0),
                                key,
                                False,
                                bitarray(int2ba(hitsounds)),
                            )
                        )
                    case _:
                        xs = line.split(":")
                        properties[xs[0]] = xs[1]

        if properties["CircleSize"] != "4":
            return None

        return properties["AudioFilename"].strip(), bpm, hit_objects
