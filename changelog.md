# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).


## 2020-03-11
### Added
- quality.sh

### Changed
- Conform to PEP8. There are heavy changes to all py files, including:
  - Rename variables.
  - Refactor long functions and nested `if` statements (add continue
    statements instead where possible).
- (minetestinfo.py) Rename the ConfigManager instance from minetestinfo
  to mti.
- Move issues from readme to
  <https://github.com/poikilos/mtanalyze/issues>.
- Improve formatting and wording of readme.


## 2017-03-25
### Added
- List all world folder names, and do not list subfolders.

### Removed
- Remove inaccurate use of os.walk in load_world_and_mod_data.


## 2017-02-16
### Added
- List players by distance.


## 2017-02-16
### Fixed
- Fix some long-standing syntax and logic errors in get_pos.
- Add missing colons in switch_player_file_contents.


## 2016-03-22
### Added
- Optionally hide player location.

### Fixed
- Detect exceptions in minetestmapper (such as database locked) and do
  NOT set is_empty as True in that case.


## 2016-03-22
### Added
- Make a method (in chunkymap.php) to echo the map as an html5 canvas.
