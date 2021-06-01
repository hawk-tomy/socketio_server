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



def event_receiver(event, event_type):
    if event_type == 'p2b':

        @sio.on(event)
        async def p2b(sid, json):
            if users['sid', sid, 'type'] != 'plugin':
                return
            sender = users['sid', sid, 'name']
            bots = users.find_notice(sender)
            for bot in bots:
                if bot['connected']:
                    await sio.emit(self.event,json,sender,to=bot['sid'])

    elif event_type == 'b2p':

        @sio.on(event)
        async def b2p(sid, json):
            to = json.pop('to',None)
            if to is None or users[to,] is None:
                await sio.emit(
                    self.event,
                    {
                        'status': 'error',
                        'message': 'key "to" is not found in this json'
                        },
                     to=sid
                     )
                return
            to_user = users[to,]
            if 'id' not in json:
                await sio.emit(
                    self.event,
                    {
                        'status': 'error',
                        'message': 'key "id" is not found in this json'
                    },
                    to=sid
                    )
                return
            if to_user['connected']:
                to_sid = to_user['sid']
                json['to'] = users['sid', request.sid, 'name']
                await sio.emit(self.event, json, to=to_sid)
            else:
                await sio.emit(
                    self.event,
                    {
                        'status': 'error',
                        'message': 'this destination is not online'
                        },
                    to=sid
                    )

    else:
        raise ValueError(f'this event {event} is not found')


for event, event_type in event_dict.items():
    event_receiver(event, event_type)


@sio.event
async def notice(sid, json):
    user = users['sid', sid]
    if user['type'] in ('bot',):
        if json['name'] not in (u['name'] for u in users.users):
            await sio.emit(
                'notice',
                {'status': 'error', 'message': 'this user is not found'}
                to=sid
                )
        elif users['name', json['name'], 'type'] == 'plugin':
            user.append('notice',json['name'])
            close_user()
            await sio.emit('notice', {'status': 'success', 'message': 'success'}, to=sid)
        else:
            await sio.emit(
                'notice',
                {'status':'error','message':'this user is not plugin'}
                to=sid
                )
    else:
        await sio.emit(
            'notice',
            {'status':'error','message':'this event is BOT only'}
            to=sid
            )


@sio.event
async def get_notice(sid):
    user = users['sid', sid]
    await sio.emit('get_notice',{'notices':user['notice']},to=sid)


@sio.event
async def login(sid, json):
    try:
        print(users)
        password = users['name', json['name'], 'password']
    except KeyError:
        await sio.emit('login_result', {'status':'error', 'message':'Bad Name'}, to=sid)
        await sio.disconnect(sid)
    else:
        if password == json['password']:
            await sio.emit('login_result', {'status':'success', 'message':'success'},to=sid)
            user = users[json['name'],]
            user['sid'] = sid
            user['connected'] = True
            close_user()
            bots = users.find_notice(user['name'])
            for bot in bots:
                if bot['connected']:
                    await sio.emit('plugin_login',user['name'],to=bot['sid'])
        else:
            await sio.emit('login_result', {'status':'error', 'message':'Bad Password'},to=sid)
            await sio.disconnect(sid)


@sio.event
async def connect(sid):
    logger.info(f'{request.sid} is connected')
    await sio.sleep(1)
    await sio.emit('message','your connection.pls wait login event',to=sid)
    await sio.emit('login',{'status':'notice','message':'please login'},to=sid)


@sio.event
async def disconnect(sid):
    logger.info(f'{request.sid} is disconnected')
    try:
        user = users['sid',sid]
    except KeyError:
        pass
    else:
        user['sid'] = None
        user['connected'] = False
        close_user()


if __name__ == '__main__':
    web.run_app(app)
