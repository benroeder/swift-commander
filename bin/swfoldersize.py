#! /usr/bin/env python3

# Script for comparing the size of a posix folder with the size of a swift pseudo folder
#
# swfoldersize.py dirkpetersen / Jan 2015 
#

import swiftclient, sys, os, argparse, math, functools

class KeyboardInterruptError(Exception): pass

def main():

    if args.container:
        c=create_sw_conn()
        print ("    checking swift folder %s/%s ..." % (args.container,args.prefix))
        headers, objects = c.get_container(args.container,prefix=args.prefix,full_listing=True)
        sbytes=0
        for obj in objects:
            sbytes+=obj['bytes']
            #print(obj['name'],obj['bytes'])
        if sbytes > 0:
            print ("    %s bytes (%s) in %s/%s (swift)" % (intwithcommas(sbytes),convertByteSize(sbytes),args.container,args.prefix))
        else:
            print ("    ...Error: it seems swift folder %s/%s does not exist" % (args.container,args.prefix))

    if args.posixfolder:
        print ("    checking posix folder %s ..." % (args.posixfolder))
        pbytes = getFolderSize(os.path.expanduser(args.posixfolder))
        print ("    %s bytes (%s) in %s" % (intwithcommas(pbytes),convertByteSize(pbytes),args.posixfolder))

    if args.posixfolder and args.container:
        if sbytes == pbytes:
            print("OK! The size of %s and %s/%s is identical!" % \
                    (args.posixfolder,args.container,args.prefix))
        else:
            print("*** WARNING !! *** The size of  %s and %s/%s is NOT identical!" % \
                    (args.posixfolder,args.container,args.prefix))

def getFolderSize(p):
    if "/.snapshot/" in p:
        return 0
    if os.path.islink(p):
    	return 0
    prepend = functools.partial(os.path.join, p)
    try:
        return sum([(os.path.getsize(f) if os.path.isfile(f) else getFolderSize(f)) for f in map(prepend, os.listdir(p))])
    except:
        print("    ...Error getting size of folder %s" % p)
        return 0

def create_sw_conn():
    swift_auth=os.environ.get("ST_AUTH")
    swift_user=os.environ.get("ST_USER")
    swift_key=os.environ.get("ST_KEY")
    if swift_auth and swift_user and swift_key:
        return swiftclient.Connection(authurl=swift_auth,user=swift_user,key=swift_key)

def convertByteSize(size):
   if size == 0:
   	return '0 B'
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size,1024)))
   p = math.pow(1024,i)
   s = size/p
   if (s > 0):
       return '%0.3f %s' % (s,size_name[i])
   else:
       return '0 B'

def intwithcommas(x):
    result=''
    while x >= 1000:
        x,r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)

def parse_arguments():
    """
    Gather command-line arguments.
    """
    parser = argparse.ArgumentParser(prog='swfoldersize.py',
        description='compare the size of a posix folder with the size ' + \
        'of a swift (pseudo) folder after a data migration ' + \
        '()')
    parser.add_argument( '--posixfolder', '-p', dest='posixfolder',
        action='store',
        help='a folder on a posix file system ',
        default='' )        
    parser.add_argument( '--container', '-c', dest='container',
        action='store',
        help='a container in the swift object store',
        default='' )
    parser.add_argument( '--prefix', '-x', dest='prefix',
        action='store',
        help='a swift object prefix',
        default=None)
    parser.add_argument( '--proc', '-m', dest='maxproc',
        action='store',
        type=int,
        help='maximum number of processes to run (not yet implemented)',
        default=0 )
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    # Parse command-line arguments
    args = parse_arguments()
    sys.exit(main())

