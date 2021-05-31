#!/usr/bin/env python3.9
from aiohttp import web
import socketio
import yaml


from util import getLogger, manager


logger = getLogger('server',saveName='server.log')
slogger = logger.getChild('sIO')
elogger = logger.getChild('eIO')


sio = socketio.AsyncServer(
    logger=slogger,
    engineio_logger=elogger,
    async_mode=async_mode,
    ping_interval=3600,
    async_mode='aiohttp'
    )
app = web.Application()
sio.attach(app)


with open('event_dict.yaml')as f:
    event_dict = yaml.safe_load(f)


with open('user.yaml')as f:
    users = manager(yaml.safe_load(f))


def close_user():
    with open('user.yaml','w')as f:
        yaml.dump(users.toSerialize(),f,canonical=False)
close_user()


def json_decorator(func):
    def decorator(json):
        if isinstance(json,(dict,list)):
            return func(json)
        else:
            logger.warning('not json')
    return decorator


class p2b():
    def __init__(self,event):
        self.event = event

    def __call__(self,json):
        sid = request.sid
        if users['sid', sid, 'type'] != 'plugin':
            return
        sender = users['sid', sid, 'name']
        bots = users.find_notice(sender)
        for bot in bots:
            if bot['connected']:
                sio.emit(self.event,json,sender,to=bot['sid'])


class b2p():
    def __init__(self,event):
        self.event = event

    def __call__(self,json):
            to = json.pop('to',None)
            if to is None or users[to,] is None:
                sio.emit(self.event,
                    {
                        'status': 'error',
                        'message': 'key "to" is not found in this json'
                        })
                return
            to_user = users[to,]
            if 'id' not in json:
                sio.emit(self.event,
                    {
                        'status': 'error',
                        'message': 'key "id" is not found in this json'
                    })
                return
            if to_user['connected']:
                to_sid = to_user['sid']
                json['to'] = users['sid', request.sid, 'name']
                sio.emit(self.event, json, to=to_sid)
            else:
                sio.emit(self.event,
                    {
                        'status': 'error',
                        'message': 'this destination is not online'
                        })


def event_receiver(event):
    event_type = event_dict.get(event)
    if event_type == 'p2b':
        handler = p2b(event)
    elif event_type == 'b2p':
        handler = b2p(event)
    else:
        raise ValueError(f'this event {event} is not found')
    return handler
[sio.on_event(e,event_receiver(e)) for e in event_dict]


@sio.event
def notice(json):
    user = users['sid', request.sid]
    if user['type'] in ('bot',):
        if json['name'] not in (u['name'] for u in users.users):
            emit('notice',
                    {'status':'error','message':'this user is not found'})
        elif users['name', json['name'], 'type'] == 'plugin':
            user.append('notice',json['name'])
            close_user()
            sio.emit('notice',{'status':'success', 'message':'success'})
        else:
            sio.emit('notice',
                    {'status':'error','message':'this user is not plugin'})
    else:
        sio.emit('notice',
                {'status':'error','message':'this event is BOT only'})


@sio.event
def get_notice():
    user = users['sid', request.sid]
    sio.emit('get_notice',{'notices':user['notice']})


@sio.event
def login(json):
    try:
        print(users)
        password = users['name', json['name'], 'password']
    except KeyError:
        sio.emit('login_result', {'status':'error', 'message':'Bad Name'})
        flask_socketio.disconnect()
    else:
        if password == json['password']:
            sio.emit('login_result', {'status':'success', 'message':'success'})
            user = users[json['name'],]
            user['sid'] = request.sid
            user['connected'] = True
            close_user()
            bots = users.find_notice(user['name'])
            for bot in bots:
                if bot['connected']:
                    sio.emit('plugin_login',user['name'],to=bot['sid'])
        else:
            sio.emit('login_result', {'status':'error', 'message':'Bad Password'})
            flask_socketio.disconnect()


@sio.event
def connect():
    logger.info(f'{request.sid} is connected')
    sio.sleep(1)
    sio.emit('message','your connection.pls wait login event')
    sio.emit('login',{'status':'notice','message':'please login'})


@sio.event
def disconnect():
    logger.info(f'{request.sid} is disconnected')
    try:
        user = users['sid',request.sid]
    except KeyError:
        pass
    else:
        user['sid'] = None
        user['connected'] = False
        close_user()


if __name__ == '__main__':
    web.run_app(app)
