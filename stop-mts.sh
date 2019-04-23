#!/bin/sh
MTS_HAYSTACK_PATH=/tmp/mts_haystack
# the space in the sed param means search for a space. The result is all characters before the space.
ps -e | grep minetestserver | sed 's/ .*//' > "$MTS_HAYSTACK_PATH"
#ps -e | grep minetestserver > "$MTS_HAYSTACK_PATH"
# as per TheOther1. linuxquestions.org.
# <http://www.linuxquestions.org/questions/programming-9/bash-shell-script-read-file-line-by-line-136784/>.
# 20 Jan 2004. 19 Feb 2016.
a=0
while read line
do a=$(($a+1));
pid=$line
#echo $pid
#echo $line | sed 's/ .*//'
kill -TERM $pid
done < "$MTS_HAYSTACK_PATH"
echo "Final line count is: $a";
rm "$MTS_HAYSTACK_PATH"
#TODO someday (?):
# ssh hostname 'kill -TERM $pid'
