def set_player_names_to_file_names():
    assignment_operator = "="
    correct_count = 0
    incorrect_count = 0
    #NOTE: uses global min_indent
    line_count = 1
    print(min_indent+"set_player_names_to_file_names:")
    if os.path.isdir(players_path):
        folder_path = players_path
        print(min_indent+"  Examining players:")
        for sub_name in os.listdir(folder_path):
            sub_path = os.path.join(folder_path,sub_name)
            if os.path.isfile(sub_path):
                if (sub_name[:1]!="."):
                    print(min_indent+"    "+sub_name)
                    #stated_name = get_initial_value_from_conf(sub_path, "name", "=")
                    stated_name = None
                    line_index = 0
                    path = sub_path
                    if path is not None:
                        if os.path.isfile(path):
                            ins = open(path, 'r')
                            lines = ins.readlines()
                            ins.close()
                            time.sleep(1)
                            os.remove(sub_path)
                            is_name_found = False
                            outs = open(sub_path, 'w')
                            #outs.seek(0)
                            print(min_indent+"    Got "+str(len(lines))+" in "+sub_name)
                            while line_count<len(lines):
                                print (min_indent+"      index "+str(line_index)+":")
                                ao_i=lines[line_index].find(assignment_operator)
                                write_line_enable = True
                                if ao_i>0:  # intentionally do not check for variable name when ao is at 0
                                    var_name = lines[line_index][:ao_i].strip()
                                    if var_name=="name":
                                        if not is_name_found:
                                            is_name_found = True
                                            stated_name = lines[line_index][ao_i+1:].strip()  #NOTE: blank is allowed
                                            if stated_name is not None:
                                                if len(stated_name)>0:
                                                    if sub_name==stated_name:
                                                        correct_count += 1
                                                        break
                                                    else:
                                                        incorrect_count += 1
                                                        print(min_indent+"      Incorrect name "+stated_name+" found in "+sub_name)
                                                else:
                                                    print(min_indent+"      WARNING: name is blank in "+sub_path)
                                            else:
                                                print(min_indent+"      WARNING: name not found in "+sub_path)
                                        else:
                                            write_line_enable = False
                                            print(min_indent+"      WARNING: Removing second name in "+sub_path)
                                if (write_line_enable):
                                    outs.write(lines[line_index]+"\n")
                                line_index += 1
                            outs.close()
                        else:
                            print(min_indent+"    ERROR in set_player_names_to_file_names: '"+str(path)+"' is not a file.")
                    else:
                        print(min_indent+"    ERROR in set_player_names_to_file_names: path is None.")

    print(min_indent+"  Summary:")  # of set_player_names_to_file_names:")
    print(min_indent+"    "+str(correct_count)+" correct name(s)")
    print(min_indent+"    "+str(incorrect_count)+" incorrect name(s)")
