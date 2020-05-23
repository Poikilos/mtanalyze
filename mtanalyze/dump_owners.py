#!/usr/bin/env python
import os

changed_flag = ".new-owner.we"

def showValues(name, path, delimiterInsideValue=None, opener='"',
               closer='"', sign="=", nameOpener='["', nameCloser='"]',
               enableOnlyUnique=True):
    # such as:
    # * `["meta"] = {["fields"] = {["owner"] = "k", ["members"] = "Saw s", ["infotext"] = "Protection (owned by k)"}, ["inventory"] = {}}`
    # * ```
    #   ["infotext"] = "Consult n's Awards\
    #   Right-click to open"}
    #   ```
    # * `["fields"] = {["infotext"] = "Protection (owned by n)", ["members"] = "a", ["owner"] = "n"},`
    # * `["meta"] = {["fields"] = {["infotext"] = "by n ", ["text"] = "by n", ["__signslib_new_format"] = "1"`
    start = 0
    nameField = nameOpener + name + nameCloser
    # Terminology:
    # raw: unprocessed, but does not include quotes
    # field: uncludes syntax of data file, such as delimiters and quotes
    uniqueValues = {}

    if enableOnlyUnique:
        print("  # only showing unique values for " + nameField)
    print("  " + name + ":")
    with open(path, 'r') as ins:
        rawLine = True
        lineNumber = 1
        thisValue = None
        thisName = None
        prevLine = None
        prevNameIndex = None
        signIndex = -1
        signEnder = -1
        continuation = None
        while rawLine:
            rawLine = ins.readline()
            if rawLine:
                line = rawLine.rstrip()  # remove newline character
                start = 0
                while start > -1:
                    # print("    - "+str(start)+"...")
                    if thisName is not None:
                        if thisValue is not None:
                            # print("    - thisValue: '"+thisValue+"'")
                            if not thisValue.endswith("\\"):
                                print("    # "+path+"("+str(lineNumber-1)+","+str(start)+"): Unexpected end of value (expected \\ for line continuation) after " + prevLine[prevNameIndex:])
                            else:
                                thisValue = thisValue[:-1]
                            # print("  - thisValue: '"+thisValue+"'"+"  # line: "+str(lineNumber))
                            openerEnderI = start  # usually 0 when thisValue is None
                            if openerEnderI != 0:
                                print("    # "+path+"("+str(lineNumber)+","+str(signEnderI)+"): continuation is not at start of line (the error is in the Python logic)")
                            closerIndex = line.find(closer, start)
                            if closerIndex > -1:
                                rawValue = line[openerEnderI:closerIndex]
                                # print("    - rawValue: '"+rawValue+"'"+"  # line: "+str(lineNumber))
                                # print("    - line[:30]: '"+line[:30]+"'")
                                # print("    - openerEnderI: '"+str(openerEnderI)+"'")
                                thisValue += " " + rawValue  # a newline counts as a space
                                start = closerIndex + len(closer)
                                values = [thisValue]
                                if delimiterInsideValue is not None:
                                    values = rawValue.split(delimiterInsideValue)
                                for v in values:
                                    v = v.strip()
                                    if len(v) > 0:
                                        thisValue = None
                                        old = uniqueValues.get(v)
                                        if (old is not True) or (not enableOnlyUnique):
                                            uniqueValues[v] = True
                                            # print("  - "+path+"("+str(lineNumber)+","+str(openerEnderI)+"): " + v)
                                            print("    '@("+str(lineNumber)+","+str(openerEnderI)+")': '" + v + "'")
                                thisValue = None  # ok since line has a closer
                            else:
                                thisValue += " " + line[openerEnderI:]  # value must be on more than 2 lines, so continue again; newline counts as space
                                start = -1
                            continuation = None
                            continue
                        if signIndex > -1:
                            continuation = "sign continuation"
                        else:
                            continuation = "name continuation"
                    else:
                        continuation = None

                    nameIndex = line.find(nameField, start)
                    if (nameIndex > -1) or (thisName is not None):
                        nameEnderI = nameIndex + len(nameField)
                        start = nameEnderI
                        prevNameIndex = nameIndex
                        if signIndex == -1:
                            signIndex = line.find(sign, nameEnderI)
                        else:
                            signIndex = 0
                            signEnder = 0
                        if signIndex > -1:
                            thisName = name
                            if signEnder == -1:
                                # only change if not a continuation
                                signEnderI = signIndex + len(sign)
                            start = signEnderI
                            openerIndex = line.find(opener, signEnderI)
                            signIndex = -1
                            signEnder = -1
                            if openerIndex > -1:
                                openerEnderI = openerIndex + len(opener)
                                start = openerEnderI
                                closerIndex = line.find(closer, openerEnderI)
                                if closerIndex > -1:
                                    rawValue = line[openerEnderI:closerIndex]
                                    start = closerIndex + len(closer)
                                    values = [rawValue]
                                    if delimiterInsideValue is not None:
                                        values = rawValue.split(delimiterInsideValue)
                                    for v in values:
                                        v = v.strip()
                                        if len(v) > 0:
                                            thisValue = None
                                            old = uniqueValues.get(v)
                                            if (old is not True) or (not enableOnlyUnique):
                                                uniqueValues[v] = True
                                                # print("    # "+path+"("+str(lineNumber)+","+str(openerEnderI)+"): " + v)
                                                print("    '@("+str(lineNumber)+","+str(openerEnderI)+")': '" + v + "'")
                                    thisValue = None
                                    thisName = None
                                else:
                                    thisValue = line[openerEnderI:]  # in case wraps to next line
                                    # print("    # waiting for continuation after '"+thisValue+"' on line " + str(lineNumber) + "...")
                                    if not thisValue.endswith("\\"):
                                        print("  "+path+"("+str(lineNumber)+","+str(openerEnderI)+"): Missing \\ " + closer + " (before continuation) after " + line[nameIndex:openerEnderI] + line[openerEnderI:])
                                    # print("    # "+path+"("+str(lineNumber)+","+str(openerEnderI)+"): Missing closing " + closer + " after " + line[nameIndex:openerEnderI] + line[openerEnderI:])
                                    start = -1
                            else:
                                print("    # "+path+"("+str(lineNumber)+","+str(signEnderI)+"): Missing opening " + opener)
                                if continuation is not None:
                                    print("    #   (during " + continuation + ")")
                        else:
                            print("    # "+path+"("+str(lineNumber)+","+str(nameEnderI)+"): Missing" + sign)
                            if continuation is not None:
                                print("    # (during " + continuation + ")")
                    else:
                        start = -1
                prevLine = line
            lineNumber += 1

def main():
    folder_path = "."
    counts = {}
    counts["we"] = 0
    for sub_name in os.listdir(folder_path):
        sub_path = os.path.join(folder_path, sub_name)
        if ((sub_name[:1]!=".") and os.path.isfile(sub_path)
                and (sub_name[-len(changed_flag):] != changed_flag)
                and (sub_name[-3:].lower() == ".we")):
            counts["we"] += 1
            print("")
            print(sub_path + ":")
            showValues("owner", sub_path)
            showValues("members", sub_path, " ")
            # showValues("infotext", sub_path, enableOnlyUnique=False)  # could be anything, such as copy of a sign's ["text"]
            showValues("infotext", sub_path)  # could be anything, such as copy of a sign's ["text"]
            showValues("text", sub_path)  # could be anything, such as copy of a sign's ["text"]
            # changedCount, lineCount = changeOwner(sub_path)
            # print("lineCount: " + str(lineCount))
            # print("changedCount: " + str(changedCount))

    for ext, count in counts.items():
        print("* there were {} {} file(s) in {}."
              "".format(count, ext, folder_path))
if __name__ == "__main__":
    main()
