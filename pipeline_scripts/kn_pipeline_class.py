
import ntpath
from scipy import io as sio
from os import listdir
from os.path import isfile, join, isdir
import json
import re
import math
import os
import sys
import re
import resource
import inspect
import subprocess
import math
import argparse #https://docs.python.org/2/library/argparse.html
import time
import datetime
import socket
import mysql.connector as mariadb
from pathlib import Path
#from kn_pipeline_common import *
from kn_common import pipetools,pipedef,switch

class CPipeError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)



class CPipeStep:

    #UPDATE `kn_pipeline_meso_unpack` SET STATE='finished' WHERE MID='R01_0039_CM703F'
    #UPDATE `kn_pipeline_meso_stitch_preview` SET STATE='failed' WHERE MID='R01_0034_CM521F'
    #UPDATE `kn_pipeline_meso_copy` SET STATE='failed' WHERE MID='R01_0034_CM521F'
    #INSERT INTO kn_pipeline_meso_init (MID,STATE) VALUES ('R01_0053_CM1061F','finished')
    #DELETE FROM `kn_pipeline_macro_init` WHERE MID='R01_0049_CM1061F'
    def __init__(self,dependencies={},**kwargs):
        this_script=os.path.abspath(__file__)
        this_folder=os.path.dirname(__file__)
        this_script_folder, this_script_fname=os.path.split(this_script)

        sys.path.append(this_folder)

        #frame = inspect.stack()[0]
        #module = inspect.getmodule(frame[0])
        for item in inspect.stack():
            if item and __file__ not in item:
                call_script_folder, call_script_fname=os.path.split(item[1])
                self.fullscriptname = this_script_folder+"/"+call_script_fname
                self.scriptname = call_script_fname
                self.this_script_folder = this_script_folder


        if (kwargs is not None) and ("shortname" in kwargs):
            self.shortname=kwargs['shortname'];
        else:
            self.shortname=self.scriptname;


        if len(dependencies)>0:
            print("#I: depends on :")
            for item in dependencies:
                print("#I: "+item)
        else:
            print("#I: no dependencies:")


        #self.WHOAMI=os.getenv('USER','WTF');
        #if self.WHOAMI=="WTF":
            #raise CPipeError("who TF are you? cannot get a useful USER id from the system")

        res, success=pipetools.bash_run("whoami");
        if not success:
            raise CPipeError("who TF are you? cannot get a useful USER id from the system")
        self.WHOAMI=res[0].replace("\n","")
        print("#I: user is "+self.WHOAMI)

        hostname=socket.gethostname()
        self.hostname=hostname
        print("#I: host is "+hostname)

        self.SLURM_JOBID=os.getenv('SLURM_JOBID','');
        if (len(self.SLURM_JOBID)>0):
            print("#I: JOB ID: "+self.SLURM_JOBID)

        self.MAX_RSYNC_TRIALS=10;
        #self.progress=0;


        self.settings={};


        self.parser = argparse.ArgumentParser()
        self.parser.add_argument("--riken_user", default="skibbe",help="riken account")
        self.parser.add_argument("--riken_key", default="~/bminds/riken_skibbe_key",help="riken ssh key location (key owner == 'runas' user) ")
        self.parser.add_argument("--id", default="None", required=True,help="MID")
        self.parser.add_argument("--runas", default="!",help="run script as a different user")
        self.parser.add_argument("--mode",default="NONE", help=argparse.SUPPRESS)
        self.parser.add_argument("--force",default="", help=argparse.SUPPRESS)
        self.parser.add_argument("--skip_computations",default="", help=argparse.SUPPRESS)
        self.parser.add_argument("--clean",default="no", help="[yes/no] clean files")
        self.parser.add_argument("--quiet",default="no", help=argparse.SUPPRESS)
        self.parser.add_argument("--rerun",default="no", help="[yes/no] rerun even if state is 'finished'")
        self.parser.add_argument("--slurm",default="yes", help="[yes/no] use the SLURM resource manager")
        self.parser.add_argument("--pipe",default="",  help=argparse.SUPPRESS)



        #parser.add_argument("--depth",default="0")



        self.cmd_string="";
        self.args = self.parser.parse_args()
        for arg in vars(self.args):
            if len(getattr(self.args, arg))>0:
                self.settings[arg]=getattr(self.args, arg)
                arg_str=" --"+arg+" "+getattr(self.args, arg);
                if (kwargs is not None) and (arg in kwargs):
                    self.settings[arg]=kwargs[arg];
                    arg_str=" --"+arg+" "+kwargs[arg];
                self.cmd_string+=arg_str
     
        self.mid=self.settings['id'];
        self.mid=self.mid.replace('\n', ' ').replace('\r', '').replace(' ','')
        if (not (len(self.mid)>0)) or (self.mid=="None"):
            raise CPipeError(""+self.mid+" is not a valid ID")

        self.ofile=pipedef.PIPELINE_OFOLDER+"/SLURM-"+format(self.mid)+"-"+self.scriptname.replace(".py","")+".txt"
        self.json_file=pipedef.PIPELINE_OFOLDER+"/SLURM-"+format(self.mid)+"-"+self.scriptname+".json"



        self.cleanup=( ('clean' in self.settings) and (self.settings['clean']=="yes") );
        self.slurm=( ('slurm' in self.settings) and (self.settings['slurm']=="yes") ) and (not self.cleanup);
        self.rerun=( ('rerun' in self.settings) and (self.settings['rerun']=="yes") );
        self.skip_computations=False;

        print("#I: MID: "+self.mid)

        if self.cleanup:
            if sys.stdout.isatty():
                if (not ( ('quiet' in self.settings) and (self.settings['quiet']=="yes") )):
                    if (not pipetools.query_yes_no("#I: really cleaning up the data")):
                        raise CPipeError("user interruption")
            print("#I: cleaning up the data for \""+self.mid+"\"")
            self.ofile=self.ofile+".clean.log"
        else:
            print("#I: checking dependencies")
            if not self.check_script_dependencies(dependencies):
                raise CPipeError("unmet dependencies for "+self.scriptname)

    def in_pipe(self):
        return ( ('pipe' in self.settings) and (self.settings['pipe']=="yes") and (not self.cleanup) and (self.slurm));

    def call_next_scripts(self,scriptnames):
        for sname in scriptnames:
            print("#I: submitting "+sname)

            cmd=self.this_script_folder+"/"+sname+" ";


            cmd+=" --riken_user "+self.settings['riken_user'];
            cmd+=" --riken_key "+self.settings['riken_key'];
            cmd+=" --id "+self.settings['id'];
            cmd+=" --runas "+self.settings['runas'];
            cmd+=" --rerun "+self.settings['rerun'];
            cmd+=" --pipe "+self.settings['pipe'];

            print("#I: "+cmd)

            SLURM_commands=[]
            SLURM_commands.append(cmd);

            if (self.slurm):
                res, success=pipetools.slurm_submit(SLURM_commands,self.ofile,name=self.mid+"-PIPE",append=True)
            else:
                print("cmd:",cmd)
                res, success=pipetools.bash_run(cmd);
            if not success:
                print("#E: "+res[1])
                raise CPipeError("submitting the next script")
            print(res[0])

    def print_settings(self):
        if self.settings is not None:
            for key, value in self.settings.items():
                print("#I: %s => %s" %(key,value))
        else:
            raise CPipeError("#E: settings empty??")

    def name(self):
        return self.scriptname;

    def pre_check(self):
        return True


    def check_script_dependencies(self,depends):
        #return pipetools.check_dependencies(depends,self.mid)

        dep_met=True;
        if len(depends) > 0:
            try:
                login_data, isfile=pipetools.json_read(str(Path.home())+"/pipeline_passwd/kakushin.json")
                assert(isfile)
                mariadb_connection = mariadb.connect(
                        host=login_data["host"],
                        user=login_data["username"],
                        password=login_data["passwd"],
                        database=login_data["database"])
                cursor = mariadb_connection.cursor()#(buffered=True)


                for dep in depends:
                    table_name=dep[0:len(dep)-3];
                    #print "#I: SQL table name: "+table_name
                    cursor.execute("SELECT * FROM "+table_name+" WHERE MID LIKE '"+self.mid+"'");
                    query=cursor.fetchall()
                    if  query:
                        if len(query)!=1:
                            print("table_name : ",table_name)
                            print("self.mid : ",self.mid)
                            for q in query:
                                print(q)
                            raise CPipeError("more than one entry with dame MID exists")
                        state=query[0][3];
                        #force_rerun=( ('force' in self.settings) and (self.settings['force']=="yes") )
                        if (state!='finished'):
                        #if (state!='finished') and (not force_rerun):
                            dep_met=False;
                            print("#W: state of "+table_name+" is "+state)

                    else:
                        dep_met=False;
                        print("#W: no data for "+table_name)

                mariadb_connection.commit()
                mariadb_connection.close()
            except mariadb.Error as error:
                print(("DB Error: {}".format(error)))
                print(pipetools.get_folder_timestamp())
                raise CPipeError("database error")
            except CPipeError as e:
                print("#W: rolling back sql commands")
                mariadb_connection.rollback()
                mariadb_connection.close()
                raise e

        force_rerun = ( ('force' in self.settings) and (self.settings['force']=="yes") )
        if (not dep_met) and force_rerun:
            print("#W: #########################################################")
            print("#W: #########################################################")
            print("#W: dependencies not met ! but forced to run. script may fail")
            print("#W: #########################################################")
            print("#W: #########################################################")
            dep_met = True
        return dep_met


    def sql_add_custome_data(self,fieldname,data,datatype="VARCHAR(5000)"):
    #def sql_add_custome_data(self,fieldname,data,datatype="TEXT"):
        try:
            login_data, isfile=pipetools.json_read(str(Path.home())+"/pipeline_passwd/kakushin.json")
            assert(isfile)
            mariadb_connection = mariadb.connect(
                    host=login_data["host"],
                    user=login_data["username"],
                    password=login_data["passwd"],
                    database=login_data["database"])
            cursor = mariadb_connection.cursor()#(buffered=True)

            table_name=self.scriptname[0:len(self.scriptname)-3].replace('\'', '\'\'');


            #print("WTF")
            if not self.sql_field_exists(mariadb_connection, fieldname):
                print("#I: custome field "+fieldname+" does not exist. adding the field to "+table_name)
                cursor.execute("ALTER TABLE "+table_name+" ADD "+fieldname+" "+datatype)

            #print("WTF")

            data_rep=data;#"REPLACE(REPLACE("+ data+ ", '\"', '\\\"'), \"'\", \"\\\'\")"
            #print "#I: setting "+fieldname+" in table "+table_name+" to "+format(data_rep)

            print("#I: setting "+fieldname+" in table "+table_name+" to custome data")
            cursor.execute("UPDATE "+table_name+" SET "+fieldname+"='"+data_rep+"' WHERE MID='"+self.mid+"'")


            mariadb_connection.commit()
            mariadb_connection.close()
        except mariadb.Error as error:
            print(("DB Error: {}".format(error)))
            print(pipetools.get_folder_timestamp())
            raise CPipeError("database error")
        except CPipeError as e:
            print("#W: rolling back sql commands")
            mariadb_connection.rollback()
            mariadb_connection.close()
            raise e

    def sql_table_exists(self,dbcon, tablename):
        dbcur = dbcon.cursor()
        dbcur.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = '{0}'
            """.format(tablename.replace('\'', '\'\'')))
        if dbcur.fetchone()[0] == 1:
            dbcur.close()
            return True

        dbcur.close()
        return False

    def sql_field_exists(self,dbcon, fieldname):
        dbcur = dbcon.cursor()
        table_name=self.scriptname[0:len(self.scriptname)-3].replace('\'', '\'\'');
        fieldname=fieldname.replace('\'', '\'\'');


        dbcur.execute("SELECT * \
        FROM information_schema.COLUMNS \
        WHERE \
            TABLE_SCHEMA = 'pipeline_db' \
        AND TABLE_NAME = '"+table_name+"' \
        AND COLUMN_NAME = '"+fieldname+"'")


        query=dbcur.fetchall()

        return not (not query)




    def update_progress_sql(self,mode="run",progress=-1):

        try:
            login_data, isfile=pipetools.json_read(str(Path.home())+"/pipeline_passwd/kakushin.json")
            assert(isfile)
            mariadb_connection = mariadb.connect(
                    host=login_data["host"],
                    user=login_data["username"],
                    password=login_data["passwd"],
                    database=login_data["database"])
            cursor = mariadb_connection.cursor()#(buffered=True)


            table_name=self.scriptname[0:len(self.scriptname)-3];
            print("#I: SQL table name: "+table_name)

            if mode=="init":
            #cursor.execute("DROP TABLE `pipeline`");
            #cursor.execute("DROP TABLE `"+table_name+"`");

            #check if pipeline table exists
                if self.sql_table_exists(mariadb_connection,'pipeline'):
                    print("#I: table 'pipeline' exists")
                    #cursor.execute("DROP TABLE `pipeline."+self.scriptname+"`");
                else:
                    print("#I: table 'pipeline' does not exist")
                    cursor.execute("CREATE TABLE `pipeline` (MID VARCHAR(100) NOT NULL)");
                    #mariadb_connection.commit()

                #check if pipestep table exists
                cursor.execute("SELECT * FROM pipeline WHERE MID LIKE '"+self.mid+"'");
                query=cursor.fetchall()
                if not query:
                    print("#I: "+self.mid+" currently not in pipline; creating entry")
                    cursor.execute("INSERT INTO pipeline VALUES ('"+self.mid+"')")
                else:
                    print("#I: "+self.mid+" in pipline")

                #print("WTF 0")
                #check if MID exists in pipestep table
                if self.sql_table_exists(mariadb_connection,table_name):
                    print("#I: table '"+table_name+"' exists")
                else:
                    print("#I: table '"+table_name+"' does not exist")
                    cursor.execute("CREATE TABLE `"+table_name+"` (\
                            MID VARCHAR(255) NOT NULL, \
                            PROGRESS FLOAT NOT NULL, \
                            NAME VARCHAR(255) NOT NULL, \
                            STATE VARCHAR(255) NOT NULL, \
                            TIME_STAMP_START DATETIME , \
                            TIME_STAMP_STOP DATETIME , \
                            JOB VARCHAR(1000) NOT NULL , \
                            JOBCHILDS VARCHAR(5000) NOT NULL \
                            ) ROW_FORMAT=DYNAMIC ");
               # print("WTF 1")


                #check if MID exists an is currently processed
                #cursor.execute("SELECT * FROM "+table_name+" WHERE MID LIKE '"+self.mid+"'");
                cursor.execute("SELECT MID,PROGRESS,NAME,STATE  FROM "+table_name+" WHERE MID LIKE '"+self.mid+"'");

                query=cursor.fetchall()

                #print format(query)

                new_entry = True
                if  query:
                    if len(query)!=1:
                        raise CPipeError("more than one entry with the same MID exists")
                    state=query[0][3];
                    force_rerun=( ('force' in self.settings) and (self.settings['force']=="yes") )
                    if ((state=='processing') or (state=='processing-batch')) and (not force_rerun):
                        print("#W: aleady in pipeline")
                        raise CPipeError(""+self.mid+" entry exists and is already processed")
                    else:
                        if (state=='failed'):
                            print("#W: pipeline failed before, running again without cleaning up")
                        if (state=='finished'):
                            if self.rerun:
                                print("#W: pipeline step was sucessful before, running again without cleaning up")
                            else:
                                print("#W: existing state is 'finished'. Skipping computations. Set the rerun flag to 'yes' to rerun the computations")
                                self.slurm=( ('pipe' in self.settings) and (self.settings['pipe']=="yes") );
                                self.skip_computations = True
                                new_entry = False
                                #raise CPipeError("existing state is 'finished'. Set the rerun flag to 'yes' to rerun the script")
                    if new_entry:
                        cursor.execute("DELETE FROM "+table_name+" WHERE MID='"+self.mid+"'")


                if new_entry:
                    #set state processing
                    print("#I: "+self.mid+" currently not in table; creating entry")
                    #cursor.execute("INSERT INTO "+table_name+" VALUES ('"+self.mid+"','0','"+self.shortname+"','processing',NOW(),NULL)")
                    cursor.execute("INSERT INTO "+table_name+"( MID,PROGRESS,NAME,STATE,TIME_STAMP_START ) VALUES ('"+self.mid+"','0','"+self.shortname+"','processing',NOW())")

            if mode=="run":
                #print "#I: RUN"
                sys.stderr.write("#I: progress :"+format(progress)+"\n");
                sys.stderr.flush();
                cursor.execute("UPDATE "+table_name+" SET PROGRESS='"+format(progress)+"' WHERE MID='"+self.mid+"'")

            if mode=="batchrun":
                print("#I: BATCHRUN")
                cursor.execute("UPDATE "+table_name+" SET STATE='processing-batch' WHERE MID='"+self.mid+"'")


            if mode=="failed":
                print("#I: FAILED")
                cursor.execute("UPDATE "+table_name+" SET STATE='failed' WHERE MID='"+self.mid+"'")

            if mode=="finalize":
                print("#I: FINALIZE")
                cursor.execute("UPDATE "+table_name+" SET PROGRESS='"+format(100)+"' WHERE MID='"+self.mid+"'")
                cursor.execute("UPDATE "+table_name+" SET STATE='finished',TIME_STAMP_STOP=NOW()  WHERE MID='"+self.mid+"'")

            if mode=="delete":
                if self.sql_table_exists(mariadb_connection,table_name):
                    print("#I: table "+table_name+" exists")
                    print("#I: REMOVE FROM TABLE")
                    cursor.execute("DELETE FROM "+table_name+" WHERE MID='"+self.mid+"'")
                else:
                    print("#W: table "+table_name+" does not exist")

            if mode=="clean":
                #check if MID exists in pipestep table
                if not self.sql_table_exists(mariadb_connection,table_name):
                    raise CPipeError("pipline does not exist in the database!")

                #check if MID exists an is currently processed
                cursor.execute("SELECT * FROM "+table_name+" WHERE MID LIKE '"+self.mid+"'");
                query=cursor.fetchall()
                if  query:
                    if len(query)==0:
                        raise CPipeError(self.mid+" not in pipline")
                    if len(query)!=1:
                        raise CPipeError(self.mid+" appears more than once in the table")
                    state=query[0][3];
                    force_rerun=( ('force' in self.settings) and (self.settings['force']=="yes") )
                    if (state=='processing') or (state=='processing-batch'):
                        if force_rerun:
                            print("#W: is curently processed, but force = yes")
                        else:
                            raise CPipeError(self.mid+" is curently processed")
                    if (state!='failed') and(state !='finished'):
                        if force_rerun:
                            print("#W: is neither failed nor finished, but force = yes")
                        else:
                            raise CPipeError(self.mid+" is neither failed nor finished")


            mariadb_connection.commit()
            mariadb_connection.close()
        except mariadb.Error as error:
            print(("#E: DB Error: {}".format(error)))
            print(pipetools.get_folder_timestamp())
            raise CPipeError("database error")
        except CPipeError as e:
            print("#W: rolling back sql commands")
            mariadb_connection.rollback()
            mariadb_connection.close()
            raise e



    #now its jason, in future +SQL?
    def update_progress(self,mode="run",progress=-1):
        self.update_progress_sql(mode,progress)

        if False: #we skip the json interface now
            if mode=="init":
                json_data, isfile=pipetools.json_read(self.json_file);
                if isfile:
                    if ("state" in json_data):
                        #if (json_data['state']!='failed'):
                            #print "#W: warning: aleady in pipeline, passed the pipeline or pipeline failed"
                        if (json_data['state']=='processing'):
                            print("#W: warning: aleady in pipeline")
                            raise CPipeError("json file "+self.json_file+" exists and is currently processed")
                        else:
                            if (json_data['state']=='failed'):
                                print("#W: warning:  pipeline failed before, running again without cleaning up")
                            if (json_data['state']=='finished'):
                                print("#W: warning:  pipeline step was sucessful before, running again without cleaning up")

                json_data={};
                json_data['steps']={"0" : 'init',"1" : self.shortname};
                json_data['name']=self.shortname;

                json_data['state']='processing'
                json_data['whoami']=self.WHOAMI;

                json_data['timestamp_start']=pipetools.get_timestamp();
                json_data["0"]=100;
                pipetools.json_write(json_data,self.json_file);

            if mode=="run":
                json_data, isfile=pipetools.json_read(self.json_file);
                if not (isfile or (json_data["0"]<100)):
                    raise CPipeError("something went wrong")

                sys.stderr.write("#I: progress :"+format(progress)+"\n");
                sys.stderr.flush();
                json_data["1"]=int(progress);
                pipetools.json_write(json_data,self.json_file);

            if mode=="failed":
                json_data, isfile=pipetools.json_read(self.json_file);
                json_data["1"]=-1;
                json_data['state']='failed';
                pipetools.json_write(json_data,self.json_file);


            if mode=="finalize":

                progress=100;
                sys.stderr.write("#I: progress :"+format(progress)+"\n");
                sys.stderr.flush();

                json_data, isfile=pipetools.json_read(self.json_file);
                json_data, isfile=pipetools.json_read(self.json_file);
                if not (isfile):
                    raise CPipeError("something went wrong")
                json_data["1"]=int(progress);
                json_data['timestamp_end']=pipetools.get_timestamp();

                json_data['state']='finished'
                pipetools.json_write(json_data,self.json_file);




    def batch_clean(self):
        raise CPipeError("please implement the batch_clean() function")
    #    pass

    def batch_run(self):
        raise CPipeError("please implement the batch_clean() function")
    #    pass
        #print "#I: SLURM JOB "+self.SLURM_JOBID+" IS RUNNING THE SCRIPT"
        #self.update_progress()


    def run(self,slurmopts={},next_scripts={}):
        if ("mode" in self.settings) and (self.settings['mode'] == "SLURM"):
            if len(self.SLURM_JOBID)>0:
                print("#I: SLURM JOB '"+self.SLURM_JOBID+"' IS RUNNING THE SCRIPT")
            else:
                print("#I: NO SLURM JOB IS RUNNING THE SCRIPT")
            try:
                if not self.cleanup:
                    if ( ('skip_computations' in self.settings) and (self.settings['skip_computations']=="yes") ):
                        print("#W: skipping computations")
                    else:
                        self.update_progress("batchrun");
                        print("#I: running scipt")
                        self.batch_run()
                        print("#I: script was successful")


                    self.update_progress("finalize");
                    print("#I: done")

                    if self.in_pipe():
                        if len(next_scripts)>0:
                            print("#I: calling next script(s) ".format(next_scripts))
                            self.call_next_scripts(next_scripts)
                        else:
                            print("#I: no further scripts to call in the pipeline")

                else:
                    self.batch_clean()
                    print("#I: done")
                    self.update_progress("delete");

            #except CPipeError as e:
            #    print "#E: error in batch_run"
            #    raise e
            except CPipeError as e:
                print("#E: error in processing the data")
                self.update_progress("failed");
                raise e
            except Exception as e:
                print("#E: unknown error in the pipeline:")
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print((exc_type, fname, exc_tb.tb_lineno))
                self.update_progress("failed");
                raise e
        else:
            #if self.settings['runas'] != self.WHOAMI:
            if ("mode" in self.settings) and (self.settings['mode'] != "USER"):
                skip_ = False
                if self.settings['runas']!="!":
                    cmd="sudo -P -i -u  "+self.settings['runas']+"  "+self.fullscriptname+" "+self.cmd_string+" --mode USER";
                else:
                    cmd="  "+self.fullscriptname+" "+self.cmd_string+" --mode USER";
                    #skip_ = True
                    #self.batch_run()
                if not skip_:
                    print("#I: user "+self.WHOAMI+" is calling script as user "+self.settings['runas'])
                    print("#I: "+cmd)
                    res, success=pipetools.bash_run(cmd);
                    if not success:
                        for m in [r for r in res if r is not None]:
                            print("#E: "+m)
                        raise CPipeError("error running the script")
                    print(res[0])
            else:
                if  ("mode" not in self.settings) or (self.settings['mode'] != "USER"):
                    raise CPipeError("unknonw run mode")

                if not self.cleanup:
                    self.update_progress(mode="init");
                else:
                    self.update_progress(mode="clean");

                print("#I: submitting the script")
                cmd=self.fullscriptname+" "+self.cmd_string+" --mode SLURM";
                if self.skip_computations:
                    cmd=cmd+" --skip_computations yes";
                SLURM_commands=[]
                SLURM_commands.append(cmd);

                #print "cmd:"+cmd+"  |"
                #print "!!!!!"+format(self.slurm)+"  "+format(debug)

                try:

                    if (self.slurm):
                        res, success=pipetools.slurm_submit(SLURM_commands,self.ofile,name=self.mid+"-"+self.shortname,**slurmopts)
                    else:
                        res, success=pipetools.bash_run(cmd);
                        #print format(res[0])
                        if res[0]:
                            print(format(res[0]))
                        if res[1]:
                            print(format(res[1]))
                        res=0;
                except:
                    if not self.cleanup:
                        self.update_progress("failed");

                    raise CPipeError("unkown error submitting the script")
                #for m in [r for r in res if r is not None]:
                #        print "#E: "+m

                if success:
                    print("#I: SUBMITTED JOB: "+format(res))
                    self.jobid=res

                    if (self.slurm):
                        self.sql_add_custome_data("JOB",self.jobid);
                else:
                    #if (str(res)!="0"):
                        #for m in [r for r in res if r is not None]:
                        #      print "#E: "+m
                    if not self.cleanup:
                        self.update_progress("failed");
                    #self.update_progress(mode="run",progress=-1)
                    raise CPipeError("error submitting the script")

    def asobi(self,slurmopts={},next_scripts={}):
        if ("mode" in self.settings) and (self.settings['mode'] == "SLURM"):
            if len(self.SLURM_JOBID)>0:
                print("#I: SLURM JOB '"+self.SLURM_JOBID+"' IS RUNNING THE SCRIPT")
            else:
                print("#I: NO SLURM JOB IS RUNNING THE SCRIPT")
            try:
                if not self.cleanup:
                    if ( ('skip_computations' in self.settings) and (self.settings['skip_computations']=="yes") ):
                        print("#W: skipping computations")
                    else:
                        print("#I: running scipt")
                        self.batch_run()
                        print("#I: script was successful")
                    print("#I: done")

                else:
                    self.batch_clean()
                    print("#I: done")

            except CPipeError as e:
                print("#E: error in processing the data")
                raise e
            except Exception as e:
                print("#E: unknown error in the pipeline:")
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print((exc_type, fname, exc_tb.tb_lineno))
                raise e
        else:
            if self.settings['runas'] != self.WHOAMI: 
                if self.settings['runas']!="!":
                    cmd="sudo -P -i -u  "+self.settings['runas']+"   "+self.fullscriptname+" "+self.cmd_string
                else:
                    cmd="  "+self.fullscriptname+" "+self.cmd_string;
                print("#I: user "+self.WHOAMI+" is calling script as user "+self.settings['runas'])
                print("#I: "+cmd)
                res, success=pipetools.bash_run(cmd);
                if not success:
                    for m in [r for r in res if r is not None]:
                        print("#E: "+m)
                    raise CPipeError("error running the script")
                print(res[0])
            else:
                print("#I: submitting the script")
                cmd=self.fullscriptname+" "+self.cmd_string+" --mode SLURM";
                if self.skip_computations:
                    cmd=cmd+" --skip_computations yes";
                SLURM_commands=[]
                SLURM_commands.append(cmd);

                if (False) and (self.slurm):
                    res, success=pipetools.slurm_submit(SLURM_commands,self.ofile,name=self.mid+"-"+self.shortname,**slurmopts)
                else:
                    res, success=pipetools.bash_run(cmd);
                    if res[0]:
                        print(format(res[0]))
                    if res[1]:
                        print(format(res[1]))
                    res=0;

                if success:
                    print("#I: SUBMITTED JOB: "+format(res))
                    self.jobid=res

                else:
                    if (str(res)!="0"):
                        for m in [r for r in res if r is not None]:
                            print("#E: "+m)
                    #self.update_progress(mode="run",progress=-1)
                    raise CPipeError("error submitting the script")

    def rsync(self,cmd,progress_scale=(0,1)):
        success=True;
        if "--info=progress2" not in cmd:
            print("#W: rsync requires the --info=progress2 option to track the progress")
            print("#W: adding the --info=progress2 option ")
            cmd="rsync --info=progress2  "+cmd
        else:
            cmd="rsync "+cmd

        print("#I: "+cmd)
        sys.stdout.flush();

        trial=1;
        while trial<self.MAX_RSYNC_TRIALS:
            if trial>1:
                sys.stderr.write("#W: lost connection, trying again in "+format(trial*trial)+" min (trial "+format(trial)+" out of "+format(self.MAX_RSYNC_TRIALS)+")")
                sys.stderr.flush();
                time.sleep( trial*trial*60 )

            proc = subprocess.Popen(cmd,
                    text=True,
                    shell=True,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,)
            sys.stderr.write("#I: trial :"+format(trial)+"\n");
            sys.stderr.flush();
            trial=trial+1;
            progress_string="";
            counter_old=-1;
            progress=0;
            suc_=True;

            while True:
                out = proc.stdout.read(1)
                if out == '' and proc.poll() != None:
                    sys.stderr.write("#W: sub process has stopped sending anything?\n");
                    sys.stderr.flush();
                    proc_out, proc_err = proc.communicate()

                    sys.stderr.write("#W: waiting for sub process to terminate ...")
                    sys.stderr.flush();
                    proc.wait()
                    #print "ERROR "+format(proc.returncode)

                    code=int(proc.returncode);
                    errorcodes={"1":"Syntax or usage error",
                          "2":"Protocol incompatibility",
                          "3":"Errors selecting input/output files, dirs",
                          "4":"Requested action not supported: an attempt was made to manipulate 64-bit files on a platform that cannot support them; or an option was specified that is supported by the client and not by the server.",
                          "5":"Error starting client-server protocol",
                          "6":"Daemon unable to append to log-file",
                          "10":"Error in socket I/O",
                          "11":"Error in file I/O",
                          "12":"Error in rsync protocol data stream",
                          "13":"Errors with program diagnostics",
                          "14":"Error in IPC code",
                          "20":"Received SIGUSR1 or SIGINT",
                          "21":"Some error returned by waitpid()",
                          "22":"Error allocating core memory buffers",
                          "23":"Partial transfer due to error",
                          "24":"Partial transfer due to vanished source files",
                          "25":"The --max-delete limit stopped deletions",
                          "30":"Timeout in data send/receive",
                          "35":"Timeout waiting for daemon connection",
                          "255":"unexplained error"};
                    if (code!=0):
                        if str(code) in errorcodes:
                            sys.stderr.write("#E: rsync: "+errorcodes[str(code)])
                        if str(code) not in ['10','11','12','14','21','23','30','35','255']:
                            raise CPipeError("rsync failed (code "+format(code)+")")
                    else:
                        progress=100;
                    sys.stderr.write("done\n")
                    sys.stderr.flush();
                    break
                if out != '':
                    if out == '%':
                        progress_string=progress_string+out;
                        try:
                            progress = float(re.search('\d*%', progress_string).group().replace("%", ""))
                        except:
                            pass

                        if (counter_old!=progress):
                            counter_old=progress
                            #print "#I: d: "+format(progress)+" : "+format(progress_scale)
                            #print "#I: p: "+format(int(progress*progress_scale[1]+100*progress_scale[0]))
                            self.update_progress("run",int(progress*progress_scale[1]+100*progress_scale[0]));

                        progress_string="";
                    else:
                        progress_string=progress_string+out;

                if len(progress_string)>1000:
                    progress_string="";

            if (progress>=100) or ((trial>2) and (progress==0)):
                trial=self.MAX_RSYNC_TRIALS;

        if progress<100:
        #code=int(proc.returncode);
        #if code!=0:
            raise CPipeError("rsync failed")
        else:
            self.update_progress("run",int(100*progress_scale[1]+100*progress_scale[0]));
            print("#I: rsync successfull")

        sys.stdout.flush();


        return success;

    #def riken_rsync_copy(self,source,dest,progress_scale=(0,1),roptions="",server="hpc.bminds.brain.riken.jp",defaults=False):
    def riken_rsync_copy(self,source,dest,progress_scale=(0,1),roptions="",server="ssb.bminds.brain.riken.jp",defaults=False):
        success=True;
        if defaults:
            roptions=" "+roptions+"  --partial --inplace --append-verify "



        roptions=" "+roptions+" -t --no-perms --no-owner --no-group --info=progress2 ";
        #roptions+=" --rsync-path /gpfs/home/"+self.settings['riken_user']+"/SOFTWARE/rsync/rsync/bin/rsync ";
        

        if format(self.settings['riken_key'])=="None":
            cmd = ""+roptions+"  -e 'ssh "+pipedef.RSYNC_SSH_OPTIONS+"' "+format(self.settings['riken_user']) \
                      +"@"+server+":"+source+" "+dest
        else:
            cmd = ""+roptions+"  -e 'ssh "+pipedef.RSYNC_SSH_OPTIONS+" -i "+format(self.settings['riken_key'])+"' "+format(self.settings['riken_user']) \
                      +"@"+server+":"+source+" "+dest

        return self.rsync(cmd,progress_scale);

    def kyoto_rsync_copy(self,source,dest,progress_scale=(0,1),roptions="",server="ssb.bminds.brain.riken.jp",defaults=False):
        success=True;
        if defaults:
            roptions=" "+roptions+"  --partial --inplace --append-verify "

        roptions=" "+roptions+" -t --no-perms --no-owner --no-group --info=progress2";
        #roptions+=" --rsync-path /gpfs/home/"+self.settings['riken_user']+"/SOFTWARE/rsync/rsync/bin/rsync ";

        if format(self.settings['riken_key'])=="None":
            cmd = ""+roptions+"  -e 'ssh "+pipedef.RSYNC_SSH_OPTIONS+"' "+source+" "+format(self.settings['riken_user']) \
                      +"@"+server+":"+dest
        else:
            cmd = ""+roptions+"  -e 'ssh "+pipedef.RSYNC_SSH_OPTIONS+" -i "+format(self.settings['riken_key'])+"' "+source+" "+format(self.settings['riken_user']) \
                      +"@"+server+":"+dest
        return self.rsync(cmd,progress_scale);


    def riken_execute(self,command,quiet=False):
        if format(self.settings['riken_key'])=="None":
            #LOGIN=format(self.settings['riken_user'])+"@hpc.bminds.brain.riken.jp"
            LOGIN=format(self.settings['riken_user'])+"@ssb.bminds.brain.riken.jp"
        else:
            #LOGIN="-i "+format(self.settings['riken_key'])+" "+format(self.settings['riken_user'])+"@hpc.bminds.brain.riken.jp"
            LOGIN="-i "+format(self.settings['riken_key'])+" "+format(self.settings['riken_user'])+"@ssb.bminds.brain.riken.jp"

        cmd="bash -c \"ssh "+LOGIN+"  '"+command+";exit;'\""
        if not quiet:
            print("#I: cmd:"+cmd)
        res, success=pipetools.bash_run(cmd);
        if  success:
            if not quiet:
                print("#I: remote command "+command+" was successful")
        else:
            if not quiet:
                print("#I: remote command "+command+" failed")
        return res, success;

    def riken_exists(self,filename,quiet=False):
        command="ls "+filename
        res, success=self.riken_execute(command);
        if  success:
            if not quiet:
                print("#I: remote file/folder "+filename+" exists")
        else:
            if not quiet:
                if "Permission denied" in res[1]:
                    print("#E: "+format(res[1]))
                    print("current user: "+os.getenv('USER','WTF'));
                else:
                    print("#I: remote file/folder "+filename+" does not exist")

        return success;

    def local_mkdir(self,dirname):
        mkdir="mkdir -p "+dirname;
        print("#I: "+mkdir)
        res , success  = pipetools.bash_run(mkdir)
        if not success:
            raise CPipeError("creating folder "+dirname+" failed ("+res[0]+")")

    def local_chgrp(self,dirname):
        #if recursice:
        #  mkdir="sudo chgrp kng "+dirname+"/ -R";
        #else:
        mkdir="sudo chgrp bia "+dirname;
        print("#I: "+mkdir)
        res , success  = pipetools.bash_run(mkdir)
        if not success:
            raise CPipeError("changing group for folder "+dirname+" failed \n("+res[0]+")\n("+res[1]+")"+"\ncmd: "+mkdir)

    def local_chmod(self,perms,dirname):
        #if recursice:
        #  mkdir="sudo chgrp kng "+dirname+"/ -R";
        #else:
        mkdir="chmod "+perms+" "+dirname;
        print("#I: "+mkdir)
        res , success  = pipetools.bash_run(mkdir)
        if not success:
            raise CPipeError("changing permissions for folder/file "+dirname+" failed \n("+res[0]+")\n("+res[1]+")"+"\ncmd: "+mkdir)


    def local_mv(self,source,dest):
        mv="mv  "+source+" "+dest;
        print("#I: "+mv)
        res , success  = pipetools.bash_run(mv)
        if not success:
            raise CPipeError("error moving "+source+" to "+dest+" ("+res[0]+")")


    def local_cd(self,dest):
        cd="cd  "+dest;
        print("#I: "+cd)
        res , success  = pipetools.bash_run(cd)
        if not success:
            raise CPipeError("error cd to "+dest+" ("+res[0]+")")



    def local_fast_unp(self,source,dest,progress_scale=(0,1),compression="--use-compress-program=/disk/k_raid/SOFTWARE/KAKUSHI-NOU//pipeline/kn_decompress.sh"):
        success=True;

        cmd = "pv  -n  "+source+" | tar  "+compression+" -x  -C "+dest;

        print("#I: "+cmd)
        sys.stdout.flush();

        trial=1;
        progress_string="";
        counter_old=-1;
        progress=0;
        suc_=True;
        output = ""

        proc = subprocess.Popen(cmd,stderr=subprocess.PIPE, stdin=subprocess.PIPE, stdout=None,shell=True)
        while proc.poll() is None:
            output = proc.stderr.readline()
            try:
                progress=float(output.replace('\n', ''))
            except:
                pass
            if (counter_old!=progress):
                counter_old=progress
                self.update_progress("run",float(progress*progress_scale[1]+100*progress_scale[0]));


        proc.wait()
        if (progress<100) or ((proc.returncode != 0)):
            raise CPipeError("unp failed: {}".format(output))
        else:
            self.update_progress("run",float(100*progress_scale[1]+100*progress_scale[0]));
            print("#I: unp successfull")

        sys.stdout.flush();


        return success;
