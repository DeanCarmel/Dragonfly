import os
import re
import shutil
import sys
from pathlib import Path

res_root_dir = sys.argv[1]
dest_res_root = sys.argv[2]
result_dirs = list(Path(res_root_dir).rglob("*[0-9].2021@*"))
for res_dir in result_dirs:
    res_files_list = list(Path(res_dir).rglob("single_connection_stat_*"))
    qdisc_files_list = list(Path(res_dir).rglob("*_qdisc.csv"))
    if res_files_list and qdisc_files_list:
        newdir = os.path.join(dest_res_root, res_dir.name)
        os.mkdir(newdir)
        for res_file in res_files_list:
            oldfile = open(res_file)
            res_lines = oldfile.readlines()
            if len(res_lines) < 9500:
                continue
            new_file = os.path.join(newdir, res_file.name)
            f = open(new_file,'w')
            f.writelines(res_lines[:9500])
        shutil.copy(qdisc_files_list[0], newdir)
    else:
        print ('b', end =" ")