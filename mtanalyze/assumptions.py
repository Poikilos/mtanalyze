
worldgen_mod_list = []
worldgen_mod_list.append("caverealms")
worldgen_mod_list.append("ethereal")
worldgen_mod_list.append("lapis")
worldgen_mod_list.append("mines")
worldgen_mod_list.append("mg")
# ^ NOTE: experimental worldgen mod delays/prevents chunk generation and
#   sometimes crashes in 0.4.13 release (tested on Windows 10)
worldgen_mod_list.append("moretrees")
worldgen_mod_list.append("moreores")
# worldgen_mod_list.append("nature_classic")
# ^ NOTE: plantlife_modpack has this and other stuff, but detecting this
#   could help since it is unique to the modpack
worldgen_mod_list.append("plantlife_modpack")
# ^ ok if installed as modpack instead of putting individual mods in
#   mods folder
worldgen_mod_list.append("pyramids")
worldgen_mod_list.append("railcorridors")
worldgen_mod_list.append("sea")
worldgen_mod_list.append("technic")
worldgen_mod_list.append("technic_worldgen")
worldgen_mod_list.append("tsm_mines")
worldgen_mod_list.append("tsm_pyramids")
worldgen_mod_list.append("tsm_railcorridors")

after_broken = {}
after_broken["default:stone"] = "default:cobble"
after_broken["default:stone_with_iron"] = "default:iron_lump"
after_broken["default:stone_with_copper"] = "default:copper_lump"
after_broken["default:stone_with_coal"] = "default:coal_lump"
after_broken["default:dirt_with_grass"] = "default:dirt"
after_broken["moreores:mineral_tin"] = "moreores:tin_lump"
after_broken["default:stone_with_mese"] = "default:mese_crystal"
after_broken["moreores:mineral_silver"] = "moreores:silver_lump"
after_broken["default:stone_with_gold"] = "default:gold_lump"
after_broken["default:stone_with_diamond"] = "default:diamond"
# TODO: this stuff could be scraped from lua such as from
# /usr/local/share/minetest/games/fca_game_a/mods/technic/
# technic_worldgen/nodes.lua
after_broken["technic:mineral_uranium"] = "technic:uranium_lump"
after_broken["technic:mineral_chromium"] = "technic:chromium_lump"
after_broken["technic:mineral_zinc"] = "technic:zinc_lump"
after_broken["technic:mineral_lead"] = "technic:lead_lump"
after_broken["technic:mineral_sulfur"] = "technic:sulfur_lump"
after_broken["caverealms:hanging_thin_ice"] = "caverealms:thin_ice"
after_broken["caverealms:stone_with_moss"] = "default:cobble"
after_broken["caverealms:stone_with_lichen"] = "default:cobble"
after_broken["caverealms:stone_with_algae"] = "default:cobble"
after_broken["caverealms:constant_flame"] = "Empty"
after_broken["fire:basic_flame"] = "Empty"
after_broken["default:water_source"] = "bucket:bucket_water"
after_broken["default:river_water_source"] = "bucket:bucket_river_water"
after_broken["default:lava_source"] = "bucket:bucket_lava"
# after_broken[""] = ""


after_broken_startswith = {}
after_broken_startswith["pipeworks:mese_tube_"] = \
    "pipeworks:mese_tube_000000"
after_broken_startswith["pipeworks:conductor_tube_off_"] = \
    "pipeworks:conductor_tube_off_1"
after_broken_startswith["pipeworks:tube_"] = "pipeworks:tube_1"
after_broken_startswith["Item pipeworks:accelerator_tube_"] = \
    "pipeworks:accelerator_tube_1"
