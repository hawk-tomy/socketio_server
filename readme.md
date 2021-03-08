# socketIOのeventとかの仕様について
eventは種類分けすると三種類。

1. 中継サーバーと送受信するevent
2. pluginからbotへの通知用のevent
3. botからpluginに聞いて、返り値を返すevent

これらごとに、送受信されるデータが微妙に異なったりするので以下を参照。

なお、一つ目に関してはpythonでハードコーディングしている。
また、二つ目、三つめはevent_list.yamlに書かれている、
event名をkey、その値がp2bなら二つ目の、b2pなら三つ目のeventになる。

## 1. 中継サーバーと送受信するevent
`login`や`login_result`など。
デフォルトの`connect`,`disconnect`,`message`も該当する。
これらについては細かな決まりがある。
1. サーバーからの値について。
    - `connect`event
        - 接続直後に送信。特に何もない。
    - `login`event
        - `{'status':'notice','message':'please login'}`
        - これについては常にこのjsonが来る。この`login`eventが発火したとき、同じイベントで、jsonを返す必要がある。以下の送信のeventを参照。
    - `login_result`event
        - 返り値は常に一つ。jsonが返るので、statusを参照してエラー判定。
        - 少なくとも名前をミスっていた場合
            - `{'status':'error', 'message':'Bad Name'}`
        - passwordをミスっていた場合
            - `{'status':'error', 'message':'Bad Password'}`
        - 成功した場合
            - `{'status':'success', 'message':'success'}`
    - `disconnect`event
        - 切断時に発生。特に何もなし。
    - `plugin_login`event
        - clientがbotで、noticeに指定してあるpluginがloginしたとき、その名前を引数に発火する。

1. サーバーへの値について。
    - `login`event
        - `{'name':'','password':''}`を送信する。返り値は上記の通り、`login_result`eventで返る。
    - `get_notice`event
        - 送り値無しで送信。送り値を指定しなくても送信できるのでそれで。
            - 返り値は、`{'notices':[]}`。ただし、botのアカウントのみ追加可能。
            なお、notice(通知)は、pluginからbotへの通知用の通知設定。
    - `notice`event
        - `{'name':''}`。`name`keyに、pluginのアカウント名を一つ入れることが可能。以上。
        - 指定した名前がなかった時
            - `{'status':'error','message':'this user is not found'}`
        - 指定した名前がpluginの名前でなかった時
            - `{'status':'error','message':'this user is not plugin'}`
        - 自分がbot出ない時
            - `{'status':'error','message':'this event is BOT only'}`
        - 成功したとき
            - `{'status':'success', 'message':'success'}`

## 2. pluginからbotへの通知用のevent
`tab_abnormal_tps`など。
1. clientがbotの場合。
    - 送信しても何も発生しない。
    - 受信のみ。なお、第一引数にjson、第二引数にstring(送り主の名前)を受け取る必要がある。
2. clientがpluginの場合。
    - 何かあったら容赦なく発火させるevent群。単一のjsonのみ送信可能。
    - 何かとは何時のことかってのは各eventごとに異なる。

## 3. botからpluginに聞いて、返り値を返すevent
`tab_now_tps`など。
1. clientがbotの場合。
    - 単一のjsonのみ送信可能。最小限の形は、`{'to':'','id':''}`。
    toの値は、送信先のpluginのname。idの値は好きに決めてよい(自由に使ってよい。)。
    - もしも、`to`のkeyが無かった時、中継サーバーから
    `{'status': 'error','message': 'key "to" is not found in this json'}`
    が返る。
    - もしも、送り先がonlineでない場合、中継サーバーから
    `{'status': 'error','message': 'this destination is not online'}`
    が返る。
2. clientがpluginの場合。
    - 単一のjsonが来る。最小の形は、`{'to':'','id':''}`。
    toとidの値は返り値にも含め無ければならない。
    - もしも、`to`のkeyが無かった時、中継サーバーから
    `{'status': 'error','message': 'key "to" is not found in this json'}`
    が返る。
    - もしも、送り先がonlineでない場合、中継サーバーから
    `{'status': 'error','message': 'this destination is not online'}`
    が返る。
