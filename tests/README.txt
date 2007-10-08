 Testing
=========

There are two sets of tests here.  The first are a collection of apps titled
"case##_description", which can be used manually with the manage command.
They each have two models.py files, "models.py.pre" and "models.py.post",
which are before-and-after snapshots in the development process.  Their
outputs should be obvious given their naming, and are useful for general
testing.

There are two extra scripts "reset_all_to_pre" and "reset_all_to_post",
to make switching back and forth between the two states easier.  To
actually test:

 1) call reset_all_to_pre
 2) call manage.py sqlreset [case##_desc] | my_db_cmd
 3) call reset_all_to_post
 4) call manage.py sqlevolve [case##_desc]

This should output the SQL required to turn one into the other.  For further
work, output the output of (4) into my_db_cmd, reset_all_to_pre, and call
sqlevolve again.


The other test is the unit test.  This will run a series of tests all at once
and generate a report.  To run them, call:

 1) ./runtests.py --settings=settings_mysql

Assuming your database is mysql.


Note that there are four settings files, one for each backend.  I symlink one
to settings.py when I'm testing via the case## apps, and pass it as an option
when calling runtests.py.  Note that since Windows doesn't support symlinks,
this technique won't work on that OS.  Windows users will have to copy the 
file manually.  (or rename or whatever)  Note that this also applies to the
"reset_all_to_XXX" scripts, as they use symlinks to swap the models.py files.

