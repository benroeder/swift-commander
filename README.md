swift-commander
===============

swift commander (swc) is a wrapper to various command line client tools 
for openstack swift cloud storage systems. The purpose of swc is 3 fold:

 - provide a very simple user interface to Linux users
 - provide a unified user interface to swiftclient, curl, etc with reasonale defaults
 - model commands after classic shell tools such as cd, ls, etc.


# Basic Operations

if swc is invoked without any options it shows a basic help page:

```
Swift Commander (swc) allows you to easily work with a swift object store.
swc supports sub commands that attempt to mimic standard unix file system tools.
These sub commands are currently implemented: (Arguments in sqare brackts are 
optional).

  swc upload <src> <targ>   -  copy file / dirs from a file system to swift
  swc download <src> <targ> -  copy files and dirs from swift to a file system
  swc cd <folder>           -  change current folder to <folder> in swift
  swc ls [folder]           -  list contents of a folder
  swc pwd                   -  display the current swift folder name
  swc rm <path>             -  delete all file paths that start with <path>
  swc cat <file>            -  download a file to TMPDIR and open it with cat
  swc more <file>           -  download a file to TMPDIR and open it with more
  swc less <file>           -  download a file to TMPDIR and open it with less
  swc mkdir <folder>        -  create a folder (works only at the root)
  swc list <folder> [filt]  -  list folder content (incl. subfolders) and filter
  swc openwith <cmd> <file> -  download a file to TMPDIR and open it with <cmd>
  swc header <file>         -  display the header of a file in swift
  swc meta <file>           -  display custom meta data of a file in swift
  swc mtime <file>          -  show the original mtime of a file before uploaded
  swc size <folder>         -  show the size of a swift or a local folder
  swc compare <l.fld> <fld> -  compare size of a local folder with a swift folder
  swc hash <locfile> <file> -  compare the md5sum of a local file with a swift file
  swc bundle <src> <targ>   -  upload src but put small files in a bundle.tar.gz
  swc unbundle <src> <targ> -  download src and unpack all bundle.tar.gz
  swc arch <src> <targ>     -  create one tar archive for each folder level
  swc unarch <src> <targ>   -  restore folders that have been archived

Examples:
  swc upload /local/folder /swift/folder
  swc compare /local/folder /swift/folder
  swc download /swift/folder /scratch/folder
  swc download /swift/folder $TMPDIR
  swc bundle /local/folder /swift/folder
  swc rm /archive/some_prefix
  swc more /folder/some_file.txt
  swc openwith emacs /folder/some_file.txt
```

## Important: What you need to know  about the Swift architecture 

 - swift does not know sub directories such as a file system. It knows containers and in containers it carries objects (which are actually files).
 - if you upload a path with many directory levels such as /folder1/folder2/folder3/folder4/myfile.pdf to swift it will cheat a little and put an object called `folder2/folder3/folder4/myfile.pdf` into a container called `folder1`. 
 - the object is just like a filename that contains a number of forward slashes. Forward slashes are allowed because swift does not know any directories and can have the / character as part of a filename. These fake folders are also called `Pseudo-Hierarchical Directories` ( http://www.17od.com/2012/12/19/ten-useful-openstack-swift-features/ ) 
 - the architecture has advantages and disadvantages. An advantage is that you can retrieve a hundreds of thousands of object names in a few seconds. The disadvantage is that a single container eventually reaches a scalability limit. Currently this limit is at about 2 million objects per container. You should not put more than 2 million files into a single container or /root_folder.
 - swift commander (swc) allows you to ignore the fact that there are containers and pseudo folders. For the most part you can just treat them both as standard directories

## Authentication

 - `swc` does not implement any authentication but uses a swift authentication environment, for example as setup by `https://github.com/FredHutch/swift-switch-account` including Active Directory integration.
 - if a swift authentication environment is found `swc` creates swift auth_tokens on the fly and uses them with RESTful tools such as curl.

### common commands and expected behavior 
 
 - swc rm <folder> works with sub strings not just folder or file names. For example if we have /folder1/folder2/file3.pdf and run `swc rm /folder1/fol` every path that starts with `/folder1/fol` would be deleted. 
 
### swc upload 

use `swc upload /local_dir/subdir /my_swift_container/subfolder` to copy data from a local or networked posix file system to a swift object store. `swc upload` wraps `swift upload` of the standard python swift client:

```
joe@box:~/sc$ swc upload ./testing /test
*** uploading ./test ***
*** to Swift_Account:/test/ ***
executing:swift upload --changed --segment-size=2147483648 --use-slo --segment-container=".segments_test" --header="X-Object-Meta-Uploaded-by:joe" --object-name="" "test" "./test"
*** please wait... ***
/fld11/file12
/fld11/file11
/fld11/fld2/fld3/fld4/file43
/fld11/fld2/fld3/fld4/file42
.

```

the swc wrapper adds the following features to `upload`:

 - --segment-size ensures that uploads for files > 5GB do not fail. 2147483648 = 2GB
 - Uploaded-by meta data keeps track of the operating system user (often Active Directory user) that upload the data
 - setting --segment-container ensures that containers that carry the segments for multisegment files are hidden if users access these containers with 3rd. party GUI tools (ExpanDrive, Cyberduck, FileZilla) to avoid end user confusion
 - --slo stands for Static Large Object and SLO's the recommended obkject type for large objects / files. 


as an addional feature you can add multiple meta-data tags to each uploaded object, which is great for retrieving archived files later:

```
joe@box:~/sc$ swc upload ./test /test/example/meta project:grant-xyz collaborators:jill,joe,jim cancer:breast
*** uploading ./test ***
*** to Swift_Account:/test/example/meta ***
executing:swift upload --changed --segment-size=2147483648 --use-slo --segment-container=".segments_test" --header="X-Object-Meta-Uploaded-by:petersen" --header=X-Object-Meta-project:grant-xyz --header=X-Object-Meta-collaborators:jill,joe,jim --header=X-Object-Meta-cancer:breast --object-name="example/meta" "test" "./test"
*** please wait... ***
example/meta/fld11/fld2/file21
example/meta/fld11/file11
.
.
/test/example/meta
``` 

These metadata tags stay in the swift object store with the data. They are stored just like other important metadata such as change data and name of the object. 

```
joe@box:~/sc$ swc meta example/meta/fld11/file13
       Meta Cancer: breast
Meta Collaborators: jill,joe,jim
  Meta Uploaded-By: petersen
      Meta Project: grant-xyz
        Meta Mtime: 1420047068.977197

```
if you store metadata tags you can later use an external search engine such as ElasticSearch to quickly search for metadata you populated while uploading data

alias: you can use `swc up` instead of `swc upload`


### swc download 

use `swc download /my_swift_container/subfolder /local/subfolder` to copy data from a swift object store to local or network storage. swc download` wraps `swift download` of the standard python swift client:
```
joe@box:~/sc$ swc download /test/example/ $TMPDIR/ 
example/meta/fld11/fld2/file21
example/meta/fld11/file11
```

alias: you can use `swc down` instead of `swc download`

### swc arch 

`swc arch` is a variation of `swc upload`. Instead of uploading the files as is, it creates a tar.gz archive for each directory and uploads the tar.gz archives. swc arch is different from default tar behavior because it does not create a large tar.gz file of an entire directory structure as large tar.gz files are hard to manage (as one cannot easily navigate the directory structure within or get quick access to a spcific file). Instead swc arch creates tar.gz files that do not include sub directories and it creates a separate tar.gz file for each directory and directory level. The benefit of this approach is that the entire directory structure remains intact and you can easily navigate it by using  `swc cd` and `swc ls`

### swc cd, swc, ls, swc mkdir 

these commands are simplified versions of the equivalent standard GNU tools and should work very similar to these tools.

### swc mtime

use `swc mtime /my_swift_container/subfolder/file` to see the modification time data from a swift object store to local or network storage. swc download` wraps `swift download` of the standard python swift client:



