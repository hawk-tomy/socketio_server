import logging


def getLogger(name, level= logging.DEBUG, saveName= None,):
    #フォーマットの定義
    formatter = logging.Formatter('{asctime};{name};{levelname};{message}',style='{')
    #ロガーの定義
    def_logger = logging.getLogger(name)
    def_logger.setLevel(level)
    if saveName is not None:
        #ファイル書き込み用
        fh = logging.FileHandler(saveName, encoding='utf-8')
        fh.setFormatter(formatter)
        fh.setLevel(logging.NOTSET)
        def_logger.addHandler(fh)
    if not '.' in name:
        #最上位ロガー専用
        warningSaveName = 'warning_' + saveName if saveName is not None else 'warning_main.log'
        fhw = logging.FileHandler(warningSaveName, encoding='utf-8')
        fhw.setFormatter(formatter)
        fhw.setLevel(logging.WARNING)
        #コンソール出力用
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        sh.setLevel(logging.NOTSET)
        #それぞれロガーに追加
        def_logger.addHandler(sh)
        def_logger.addHandler(fhw)
    #return def_logger
    return def_logger


class user():
    __map =  (
        ('name', None),
        ('password', None),
        ('type', None),
        ('notice', tuple()),
        ('sid', None),
        ('connected', False),
        ('list', tuple()),
        #list is (eventname, data, name) or (eventname, data, name, request_id)
        )
    __index = tuple(map(lambda e: e[0], __map))
    __default = tuple(map(lambda e: e[1], __map))


    def __init__(self, *args, **kwargs):
        if (i_l := len(self.__index)) != len(self.__default):
            raise ValueError('index length is not equal default length')
        if (a_l := len(args)) > i_l:
            raise ValueError('args is longer than index')
        if len(kwargs) > i_l:
            raise ValueError('kwargs is longer than index')
        if a_l != i_l:
            args += self.__default[a_l - i_l:]
        args = list(args)
        for k,v in kwargs.items():
            if k in self.__index:
                i = self.__index.index(k)
                args[i] = v
        self.__data = args


    def __repr__(self):
        index = self.__index
        default = self.__default
        data = self.__data
        index_list = [f'{e}: ({default[i]}, {data[i]})'
                for i, e in enumerate(index)]
        return '<user class, (index:(default,data)): 'f'{", ".join(index_list)}>'



    def __getitem__(self, key):
        if isinstance(key, str):
            if key in (i := self.__index):
                return self.__data[i.index(key)]
            else:
                raise KeyError(f'this key : ({key}) is not found.')
        else:
            raise TypeError(f'this class : ({type(key)})  is not supported.')


    def __setitem__(self, key, value):
        if isinstance(key, str):
            if key in (i := self.__index):
                self.__data[i.index(key)] = value
            else:
                raise KeyError(f'this key : ({key}) is not found.')
        else:
            raise TypeError(f'this class: ({type(key)})  is not supported.')


    def __len__(self):
        return len(self.__index)


    def __contains__(self, item):
        return item in self.__index


    @classmethod
    @property
    def getIndex(cls):
        return cls.__index


    @classmethod
    @property
    def getDefault(cls):
        return cls.__default


    @property
    def getData(self):
        return tuple(self.__data)


    def getMap(self):
        return {k:(list(e) if isinstance(e,tuple) else e)
                for k,e
                    in zip(self.__index,self.__data)}


    def append(self,key,value):
        if key not in ('notice','list'):
            raise KeyError('this key is not found')
        i = self.__index.index(key)
        data = list(self.__data[i])
        data.append(value)
        self.__data[i] = tuple(data)


class manager():
    def __init__(self,ul):
        if type(ul) is list:
            self.__users = [user(**u) for u in ul if type(u) is dict]
        else:
            raise ValueError('argument is not list')


    def __repr__(self):
        users = ['\n  '+repr(u) for u in self.__users]
        return '<manager class, users:('f'{",".join(users)}''\n  )>'


    def __getitem__(self,key):
        if type(key) is str:
            if key in user.getIndex:
                return {e[key]: e for e in self.__users}
            else:
                raise KeyError(f'this key : ({key}) is not found.')
        elif type(key) is tuple:
            if (l := len(key)) == 1:
                findeds = [u for u in self.__users if u['name'] == key[0]]
                if findeds:
                    return findeds[0]
                else:
                    raise KeyError(f'this key 0 : ({key[0]}) is not found.')
            elif l == 2:
                findeds = [u for u in self.__users if u[key[0]] == key[1]]
                if findeds:
                    return findeds[0]
                else:
                    raise KeyError(f'this key 1 : ({key[1]}) is not found.')
            elif l == 3:
                findeds = [u for u in self.__users if u[key[0]] == key[1]]
                if findeds:
                    return findeds[0][key[2]]
                else:
                    raise KeyError(f'this key 1 : ({key[1]}) is not found.')
            else:
                raise ValueError(f'this tuple length : ({len(key)}) is too big.')
        else:
            raise TypeError(f'this class : ({type(key)})  is not supported.')


    def __setitem__(self,key,item):
        if type(key) is tuple:
            if len(key) == 3:
                findeds = [u for u in self.__users if u[key[0]] == key[1]]
                if findeds:
                    findeds[0][key[2]] = item
                else:
                    raise KeyError(f'this key 1 : ({key[1]}) is not found.')
            else:
                raise ValueError(f'this tuple length : ({len(key)}) is not 3.')
        else:
            raise TypeError(f'this class : ({type(key)})  is not supported.')


    def __len__(self):
        return len(self.__users)


    def __contains__(self, item):
        if (t := type(item)) is user:
            return item in self.__users
        elif t is str:
            return item in [u['name'] for u in self.__users]


    @property
    def users(self):
        return tuple(self.__users)


    def toSerialize(self):
        return [u.getMap() for u in self.__users]


    def append(self,*args,**kwargs):
        self.__users.append(user(*args,**kwargs))


    def find_notice(self,name):
        users = []
        for user in self.__users:
            if not user['connected'] or user['type'] != 'bot':
                continue
            if name in user['notice']:
                users.append(user)
        return users
