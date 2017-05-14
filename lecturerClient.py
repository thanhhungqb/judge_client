#!/bin/python3

import argparse
import base64
import json
import pprint
import time

import requests
import sys

config = None
host = 'http://www.cse.hcmut.edu.vn'


def main():
    """ this function is called from command line which call web service to make, configure, update tasks on online system
    
    Please function for more details about parameters

    to add new assignment to system
      1. make configure file (ini) and zip of grade folder
      2. call: updateTask inifile zip_file
      3. add students, call: addUsersGroup stulist.txt
          stulist include many line: with format: studentID,groupname
      4. allow groupname to submit:
          addPermit gname assignment_name open close
          open and close format: 'yyyy-mm-dd hh:MM:ss' must include '' or ""
      
      note: lecturer must be check before allow students submit by add group 'test', all lecturer and TA share this group
      to test assignment files, groupName not include SPACE, suggest format HK-Sub-name e.g. 162-KTLT-a3
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--configfile', dest="configure_file", default="lecturer_client.json")
    subparsers = parser.add_subparsers(dest="subcommand")  # this line changed

    subparsers.add_parser('getTasks', help="View all task with id in system (right problem)")
    # subparsers.add_parser('getTask', help="get Task zip file").add_argument('name')

    foo_parser = subparsers.add_parser('updateTask', help="Add or update task")
    foo_parser.add_argument('--taskconfig', help="Task config", default="taskconfig.ini")
    foo_parser.add_argument('--zipgrade', help="Zip file of grade", default="grade.zip")

    report_task = subparsers.add_parser('reportByTaskName', help="Get report by task name")
    report_task.add_argument('name')

    # group manager
    subparsers.add_parser('getGroups', help="show all user groups")
    subparsers.add_parser('cleanGroup', help="clean a group by name").add_argument('name')

    subparsers.add_parser('getUsersByGroup', help="Get all user in a group by name").add_argument('name')

    aug = subparsers.add_parser('addUsersGroup', help="file with many line which format: user,group")
    aug.add_argument('file')

    # permit: allow to submit open, close time
    subparsers.add_parser('getPermits',
                          help="Show all permit to submit in system including: group name, task id, open and close time")

    permit_ = subparsers.add_parser('addPermit',
                                    help="include group name, task name and open, close time, please see format of time")
    permit_.add_argument('gname')
    permit_.add_argument('tname')
    permit_.add_argument('open')
    permit_.add_argument('close')

    subparsers.add_parser('getResultToken', help="For long time task").add_argument('token')

    args = parser.parse_args()

    print('subcommand', args.subcommand, args)

    try:
        with open(args.configure_file, 'r') as f:
            config = json.loads(f.read())
    except Exception as e:
        print('err', str(e))

    with NetworkUtils(config) as nut:
        try:
            ret = json.loads(nut.sendData({'username': config['username'], 'password': config['password']},
                                          url=host + '/onlinejudge/ws/auth'))
            print('ret', ret)
            r_code = ret['code']
            print('code', r_code)
            if r_code != 0:
                raise Exception('Fail when authenticate')
            config['token'] = ret['token']

        except Exception as e:
            print(e)
            sys.exit(0)

        # TASK
        if args.subcommand == 'getTasks':
            ret = json.loads(nut.sendData(packData(config, 'getTasks', {})))
            print(ret)
            for o in ret['dataout']:
                print(o)

        if args.subcommand == 'getTask':  # task name
            out = nut.sendData(packData(config, 'getTask', {'tname': args.name}))
            print(out)
            open('gr.zip', 'wb').write(base64.b64decode(out['dataout']['gradefolder']))
            out['dataout']['gradefolder'] = None

        if args.subcommand == 'updateTask':
            out = nut.sendData(packData(config, 'updateTask',
                                        {'config': filetoSend(args.taskconfig),
                                         'gradefolderzipct': filetoSend(args.zipgrade)}))
            print(out)

        # REPORT
        if args.subcommand == 'reportByTaskName':  # name
            ret = nut.sendData(packData(config, 'reportByTaskName', {'tname': args.name}))
            print(ret)
            ret = json.loads(ret)
            args.subcommand = 'getResultToken'
            args.token = ret['token']

        # USER, GROUP
        if args.subcommand == 'getGroups':
            ret = json.loads(nut.sendData(packData(config, 'getGroups', {})))
            for o in ret['dataout']:
                print(o)

        if args.subcommand == 'cleanGroup':  # name
            ret = nut.sendData(packData(config, 'cleanGroup', {'gname': args.name}))
            print(ret)

        if args.subcommand == 'addUsersGroup':  # file name: user,group in each line
            ret = nut.sendData(packData(config, 'addUsersGroup', {
                'lst': [(line.split(',')[0].strip(), line.split(',')[1].strip()) for line in open(args.file, 'r') if
                        line.strip() != ""]}))
            print(ret)
        if args.subcommand == 'getUsersByGroup':  # groupName
            out = nut.sendData(packData(config, 'getUsersByGroup', {'gname': args.name}))
            print(out)

        # PERMIT
        if args.subcommand == 'showAllPermit' or args.subcommand == 'getPermits':
            ret = json.loads(nut.sendData(packData(config, 'showAllPermit', {})))
            # print(ret)
            for o in ret['dataout']:
                print(o)

        if args.subcommand == 'addPermit':  # add new or update permit; parameters: gname, tname, open, close
            out = nut.sendData(packData(config, 'addPermit',
                                        {'gname': args[0], 'tname': args[1], 'gopen': args[2], 'gclose': args[3]}))
            print(out)

        if args.subcommand == 'getResultToken':
            is_done = False
            while not is_done:
                out = nut.sendData(packData(config, 'getResultToken', {'token': args.token}))
                out = json.loads(out)
                print(out)
                if out.get('status', None) is not None:
                    print(out['status'])
                    time.sleep(10)
                    pprint.pprint(out)                
                try:
                    f = open('t.zip', 'wb')
                    f.write(base64.b64decode(out['dataout']['content']))
                    f.close()
                    print('done')
                    is_done = True
                except:
                    pass


def packData(config, action, params):
    """
    Pack data to send
    :param config:
    :param action:
    :param params:
    :return:
    """
    return {  # 'authenicate': {'username': config['username'], 'password': config['password']},
        'token': config['token'],
        'data': {'action': action, 'params': params}}


def encodeBin(binData):
    # base64.b64encode(json.dumps(mconfig).encode('utf-8'))
    pass


def decodeBin(binData):
    pass


# define function
def mreadfile(path):
    file = open(path, 'rb')
    file_content = file.read()
    file.close()
    return file_content


def filetoSend(path):
    return base64.b64encode(mreadfile(path)).decode('utf-8')


class NetworkUtils:
    """setup url, protocol, publickey"""

    def __init__(self, config):
        self.config = config
        self.callInit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def callInit(self):
        """"""
        # print(self.config)   

    def sendData(self, load, url=None):
        print('load', load)
        if url is None:
            url = host + '/onlinejudge/ws/lecturerws'
        headers = {'content-type': 'application/json; charset=utf-8'}

        r = requests.post(url, data=json.dumps(load), headers=headers, verify=False)

        out = r.text.strip().replace('\n', ' ').replace('\n', ' \\n')
        return out

        #########################################################


if __name__ == '__main__':
    main()
