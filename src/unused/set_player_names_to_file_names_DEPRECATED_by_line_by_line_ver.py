def set_player_names_to_file_names():
    ao = "="  # assignment operator
    correct_count = 0
    incorrect_count = 0
    # NOTE: uses global min_indent
    line_count = 1
    print(min_indent+"set_player_names_to_file_names:")
    if os.path.isdir(players_path):
        folder_path = players_path
        print(min_indent+"  Examining players:")
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path, sub_name)
            if not os.path.isfile(sub_path):
                continue
            if sub_name.startswith("."):
                continue
            print(min_indent+"    "+sub_name)
            # stated_name = get_initial_value_from_conf(sub_path,
            #                                           "name", "=")
            stated_name = None

            path = sub_path
            if path is None:
                print(min_indent + "    ERROR in"
                      " set_player_names_to_file_names:"
                      " path is None.")
                continue
            if not os.path.isfile(path):
                print(min_indent + "    ERROR in"
                      " set_player_names_to_file_names: '"
                      + str(path) + "' is not a file.")
                continue
            lines = None
            with open(path, 'r') as ins:
                lines = ins.readlines()
            time.sleep(.25)
            os.remove(sub_path)
            is_name_found = False
            with open(sub_path, 'w') as outs:
                # outs.seek(0)
                print(min_indent+"    Got "+str(len(lines))+" in "+sub_name)
                line_i = -1
                # ^ increment line_i at loop start to allow continue
                while line_count < len(lines):
                    line_i += 1
                    print(min_indent+"      index "+str(line_i)+":")
                    ao_i = lines[line_i].find(ao)
                    if ao_i <= 0:
                        # Intentionally do not check for variable
                        # name when ao is at 0.
                        outs.write(lines[line_i] + "\n")
                        continue

                    var_name = lines[line_i][:ao_i].strip()
                    if var_name != "name":
                        outs.write(lines[line_i] + "\n")
                        continue
                    if is_name_found:
                        # do not write line
                        print(min_indent
                              + "      WARNING: Removing second"
                              " name in " + sub_path)
                        continue
                    is_name_found = True
                    # ^ If this line is not the name, continue
                    #   already occured above, so this is now True.
                    stated_name = lines[line_i][ao_i+1:].strip()
                    # NOTE: blank is allowed for stated_name
                    if stated_name is not None:
                        if len(stated_name) > 0:
                            if sub_name == stated_name:
                                correct_count += 1
                                break
                            else:
                                incorrect_count += 1
                                print(min_indent
                                      + "      Incorrect name "
                                      + stated_name + " found in "
                                      + sub_name)
                        else:
                            print(min_indent
                                  + "      WARNING: name is blank"
                                  " in " + sub_path)
                    else:
                        print(min_indent + "      WARNING: name not"
                              " found in " + sub_path)
                    outs.write(lines[line_i] + "\n")

    print(min_indent + "  Summary:")
    # of set_player_names_to_file_names:")
    print(min_indent + "    " + str(correct_count)
          + " correct name(s)")
    print(min_indent + "    " + str(incorrect_count)
          + " incorrect name(s)")
