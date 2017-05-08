#!/bin/python3

# this is lecture utils to process some actions needed by lecturer
import pprint
import sys
import base64
import json
import requests
import argparse
import time

config = None
host = 'http://www.cse.hcmut.edu.vn'


def main(args):
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
    global config

    if config is None:
        print('please check lecturer_client.json')
        sys.exit(0)

    parser = argparse.ArgumentParser(description='NA')
    parser.add_argument('-a', '--action', default='getTasks',
                        help='action to be run: getTasks/getTask/updateTask/addPermit/reportByTaskName')
    parser.add_argument('-p', '--par', metavar='param', type=str, nargs='+',
                        help='parameters by order, each action have some require parameter')

    args = parser.parse_args()

    action = args.action  # args[0]
    args = args.par  # args[1:]

    with NetworkUtils(config) as nut:
        # TASK
        if action == 'getTasks':
            ret = json.loads(nut.sendData(packData(config, 'getTasks', {})))
            print(ret)
            for o in ret['dataout']:
                print(o)

        if action == 'getTask':  # task name
            out = nut.sendData(packData(config, 'getTask', {'tname': args[0]}))
            open('gr.zip', 'wb').write(base64.b64decode(out['dataout']['gradefolder']))
            out['dataout']['gradefolder'] = None
            print(out)

        if action == 'updateTask':  # inifile, zip file TODO test
            out = nut.sendData(packData(config, 'updateTask',
                                        {'config': filetoSend(args[0]),
                                         'gradefolderzipct': filetoSend(args[1])}))
            print(out)

        # REPORT
        if action == 'reportByTaskName':  # name
            ret = nut.sendData(packData(config, 'reportByTaskName', {'tname': args[0]}))
            print(ret)
            ret = json.loads(ret)
            # f = open('t.zip', 'wb')
            # f.write(base64.b64decode(ret['dataout']['content']))
            # f.close()
            # print('done')
            action = 'getResultToken'
            args[0] = ret['token']

        if action == 'reportByTask':
            zipfile = nut.sendData(packData(config, 'reportByTask', {'tid': args[0]}))  # id
            print(zipfile)
            f = open('out.zip', 'wb')
            f.write(base64.b64decode(zipfile['dataout']['content']))
            f.close()
            print('done')

        if action == 'reportByTaskLastest':  # id  (only get lastest)
            zipfile = nut.sendData(packData(config, 'reportByTaskLastest', {'tid': args[0]}))
            f = open('t.zip', 'wb')
            f.write(base64.b64decode(zipfile['dataout']['content']))
            f.close()
            print('done')

        # USER
        # input file: many line, one line include user,group
        if action == 'getGroups':
            ret = json.loads(nut.sendData(packData(config, 'getGroups', {})))
            for o in ret['dataout']:
                print(o)

        if action == 'cleanGroup':  # name
            ret = nut.sendData(packData(config, 'cleanGroup', {'gname': args[0]}))
            print(ret)

        if action == 'addUsersGroup':  # file name: user,group in each line
            ret = nut.sendData(packData(config, 'addUsersGroup', {
                'lst': [(line.split(',')[0].strip(), line.split(',')[1].strip()) for line in open(args[0], 'r')]}))
            print(ret)
        if action == 'getUsersByGroup':  # groupName
            out = nut.sendData(packData(config, 'getUsersByGroup', {'gname': args[0]}))
            print(out)

        # PERMIT
        if action == 'showAllPermit' or action == 'getPermits':
            ret = json.loads(nut.sendData(packData(config, 'showAllPermit', {})))
            # print(ret)
            for o in ret['dataout']:
                print(o)

        if action == 'addPermit':  # add new or update permit; parameters: gname, tname, open, close
            out = nut.sendData(packData(config, 'addPermit',
                                        {'gname': args[0], 'tname': args[1], 'gopen': args[2], 'gclose': args[3]}))
            print(out)

        if action == 'getResultToken':
            is_done = False
            while not is_done:
                out = nut.sendData(packData(config, 'getResultToken',
                                            {'token': args[0]}))
                out = json.loads(out)
                # print(out)
                pprint.pprint(out)
                if out.get('status', None) is not None:
                    print(out['status'])
                    time.sleep(10)
                try:
                    f = open('t.zip', 'wb')
                    f.write(base64.b64decode(out['dataout']['content']))
                    # f.write(out['dataout']['content'].encode('ascii'))
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
    return {'authenicate': {'username': config['username'], 'password': config['password']},
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

    def sendData(self, load):
        print(load)
        url = host + '/onlinejudge/ws/lecturerws'
        headers = {'content-type': 'application/json; charset=utf-8'}

        r = requests.post(url, data=json.dumps(load), headers=headers, verify=False)

        out = r.text.strip().replace('\n', ' ').replace('\n', ' \\n')
        return out

        #########################################################


# entry point
# sys.argv
# argv 1 is name of action, argv 2, 3... is more details
print(str(sys.argv))

if __name__ == '__main__':
    with open('lecturer_client.json', 'r') as f:
        config = json.loads(f.read())

    main(sys.argv[1:])
