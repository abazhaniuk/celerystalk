from celery import chain
import lib.db
import lib.utils
import tasks
from celery.utils import uuid
import os
from lib import config_parser, utils

def does_aquatone_folder_exixst():
    workspace = lib.db.get_current_workspace()[0][0]
    outdir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
    aquatone_dir = os.path.join(outdir, 'celerystalkReports/aquatone/')

    try:
        os.stat(aquatone_dir)
        return True
    except:
        return False

def screenshot_command(arguments):
    if arguments["-w"]:
        output_dir, workspace = lib.workspace.create_workspace(arguments["-w"], arguments)
    else:
        try:
            workspace = lib.db.get_current_workspace()[0][0]
            output_dir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
        except:
            print("[!] There are no workspaces yet. Create one and run your command again:\n\n")
            print("./celerystalk workspace create -o output_dir -w workspace_name -m vapt")
            print("./celerystalk workspace create -o output_dir -w workspace_name -m bb\n")
            exit()

    # lib.screenshot.screenshot_all_paths(workspace)
    paths_len = len(lib.db.get_all_paths(workspace))
    print("[+]\n[+] Tasking aquatone to take [{0}] screenshots").format(str(paths_len))
    lib.screenshot.aquatone_all_paths(workspace)


def aquatone_all_paths(workspace,simulation=None,config_file=None):
    #print("in aquatone all_paths")
    urls_to_screenshot = []
    #TODO: Instead of just grabbing all paths here, maybe add some logic to see if only new paths should be scanned or something. at a minimum, as they are grabbed, we need to update the "screenshot taken" column and put the auatone directory or something like that.
    paths = lib.db.get_all_paths(workspace)
    celery_path = lib.db.get_current_install_path()[0][0]
    outdir = lib.db.get_output_dir_for_workspace(workspace)[0][0]
    outdir = os.path.join(outdir,'celerystalkReports/aquatone/')

    try:
        os.stat(outdir)
    except:
        os.makedirs(outdir)

    if config_file == None:
        config_file = "config.ini"

    config, supported_services = config_parser.read_config_ini(config_file)


    if len(paths) > 0:
        screenshot_name = "db"
        for (cmd_name, cmd) in config.items("screenshots"):
            #print(cmd_name, cmd)
            try:
                if cmd_name == "aquatone":
                    populated_command = celery_path + "/celerystalk db paths_only limit | " + cmd.replace("[OUTPUT]", outdir)
                    #print(populated_command)
            except Exception, e:
                print(e)
                print("[!] Error: In the config file, there needs to be one (and only one) enabled aquatone command.")
                exit()


        task_id = uuid()
        utils.create_task(cmd_name, populated_command, workspace, outdir + "/aquatone_report.html", workspace, task_id)
        result = chain(
            tasks.run_cmd.si(cmd_name, populated_command, celery_path, task_id).set(task_id=task_id),
        )()
        print("[+]\t\tTo keep an eye on things, run one of these commands: \n[+]")
        print("[+]\t\t./celerystalk query [watch]")
        print("[+]\t\t./celerystalk query brief [watch]")
        print("[+]\t\t./celerystalk query summary [watch]")
        print("[+]")
        print("[+] To peak behind the curtain, view log/celeryWorker.log")
        print("[+] For a csv compatible record of every command execued, view log/cmdExecutionAudit.log\n")