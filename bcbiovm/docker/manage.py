"""Manage stopping and starting a docker container for running analysis.
"""
from __future__ import print_function
import grp
import os
import pwd
import subprocess

def run_bcbio_cmd(image, mounts, bcbio_nextgen_cl):
    """Run command in docker container with the supplied arguments to bcbio-nextgen.py.
    """
    mounts = " ".join("-v %s" % x for x in mounts)
    cmd = ("docker run -d -i -t {mounts} {image} "
           "/bin/bash -c '" + user_create_cmd() +
           "bcbio_nextgen.py {bcbio_nextgen_cl}"
           "\"'")
    process = subprocess.Popen(cmd.format(**locals()), shell=True, stdout=subprocess.PIPE)
    cid = process.communicate()[0].strip()
    try:
        print("Running in docker container: %s" % cid)
        subprocess.call("docker attach -nostdin %s" % cid, shell=True)
    except:
        print ("Stopping docker container")
        subprocess.call("docker kill %s" % cid, shell=True)

def user_create_cmd(chown_cmd=""):
    """Create a user on the docker container with equivalent UID/GIDs to external user.
    """
    user = pwd.getpwuid(os.getuid())
    group = grp.getgrgid(os.getgid())
    container_bcbio_dir = "/usr/local/share"
    homedir = "/home/{user.pw_name}".format(**locals())
    cmd = ("addgroup --quiet --gid {group.gr_gid} {group.gr_name} && "
           "useradd -m -d {homedir} -s /bin/bash -g {group.gr_gid} -o -u {user.pw_uid} {user.pw_name} && "
           + chown_cmd +
           "su - -s /bin/bash {user.pw_name} -c \"cd {homedir} && "
           + proxy_cmd())
    return cmd.format(**locals())

def proxy_cmd():
    """Pass external proxy information inside container for retrieval.
    """
    out = "git config --global url.https://github.com/.insteadOf git://github.com/ && "
    if "HTTP_PROXY" in os.environ:
        out += "export HTTP_PROXY=%s && " % os.environ["HTTP_PROXY"]
    if "http_proxy" in os.environ:
        out += "export http_proxy=%s && " % os.environ["http_proxy"]
    if "HTTPS_PROXY" in os.environ:
        out += "export HTTPS_PROXY=%s && " % os.environ["HTTPS_PROXY"]
    if "https_proxy" in os.environ:
        out += "export https_proxy=%s && " % os.environ["https_proxy"]
    if "ALL_PROXY" in os.environ:
        out += "export ALL_PROXY=%s && " % os.environ["ALL_PROXY"]
    if "all_proxy" in os.environ:
        out += "export all_proxy=%s && " % os.environ["all_proxy"]
    return out
