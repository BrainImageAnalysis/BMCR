#for i in `cat sync_files.txt`; do
#    rsync -pva ../pipeline_local/$i#
#
#done

rsync -av --files-from=sync_files.txt ../pipeline_local/ ./pipeline_scripts/