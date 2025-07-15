# SkyDraw
完璧じゃないBluesky落書きアプリ

<img src="https://cdn.bsky.app/img/feed_fullsize/plain/did:plc:pkhdd7vr3zruq3uszwqunews/bafkreic2wdtqbr3riaaz2eja3eelzkapezd7wokmjbeg3yucboz2kx7rxq@jpeg" alt="sampleImage1" width="256"/> <img src="https://cdn.bsky.app/img/feed_fullsize/plain/did:plc:pkhdd7vr3zruq3uszwqunews/bafkreia67hg7rpfdvrjknsvinph2ytirmd7mlkakrbenen2vsamyftavbe@jpeg" alt="sampleImage2" width="256"/> <img src="https://cdn.bsky.app/img/feed_fullsize/plain/did:plc:pkhdd7vr3zruq3uszwqunews/bafkreiez5ta2xdwsvc4xwpjsubxiq2vmsveydzlwqiaydlargwo67znxri@jpeg" alt="sampleImage3" width="256"/>

[最新のリリースはこちらから](https://github.com/iamsako/SkyDraw/releases/latest) 
(今のところWindows用ビルドだけですが、ソースコードなら他のプラットフォームでも動くかもしれません)

## 設定
**前準備:** 
このアプリを使うために、[Ghostscript](https://ghostscript.com/)をインストールする必要があります。Tkinter(PythonのGUIフレームワーク)が.eps形式でキャンバスを保存しているので、それを普通の画像の形式に変換して投稿できるようにするのに使います。

ダウンロードページから"Ghostscript"を選び、使っているOSに合わせた"Ghostscript AGPL Release"をダウンロードしてください。(その下のGhostPCLとかXPSとかではありません)

ダウンロード・インストールが完了したら、システム環境変数のPathに"...\gs\gs(version)\bin"が追加されていることを確認してください。(この文の意味が分からなくても、インストーラーがよしなにやってくれているはずなので、たぶん大丈夫です)

他の手段が見つかったら、この準備はやらなくてもいいようにしたいと思っています。

そのあとは：
- (releaseからダウンロードした場合) zipを解凍する
- config.iniを開く
- Blueskyのハンドル(@を除いたもの)を "bsky_handle =" の後ろに入力
- Blueskyの[アプリパスワード](https://bsky.app/settings/app-passwords)を "app_password =" の後ろに入力
- デフォルトでは、アプリからの投稿は英語と日本語のタグが付きます。1つの言語だけにしたい場合は、[ISO language code](https://www.w3schools.com/tags/ref_language_codes.asp)を"language ="の後に入力してください。もし他に複数の言語でタグを付けたい場合は、ソースコードを編集してください。

設定済みのiniファイルはこんな感じになります：
```
[Login]
bsky_handle = yourcoolname.bsky.social
app_password = abcd-1234-efgh-5678

[Misc]
language = en
```

iniファイルの設定が済んだら、保存をして、exeファイル(またはmain.py)を実行してください。
アプリがうまくログインできたら、"Post to Bluesky"ボタンが青くなって、プロフィール画像が表示されます(とても小さく)。やったね！

## 使い方
- 右クリックで消す
- ブラシと消しゴムの大きさをスライダーで変更
- キャプションとaltテキストを、下側のテキストボックスで入力できる
- "Clear Canvas"(キャンバスを消す)ボタンで、えーと…
- "Post to Bluesky"(Blueskyに投稿)ボタンで…キャンバスを消す…？ (訳注：投稿時にキャンバスが消える仕様です。終わったことは終わったこと、だそうです)
- TIP: キャンバスの端っこに何かを描きたいけど、ミスって他のもの(閉じるボタンとか…)をクリックしたくないときは、ウィンドウを大きくしてみてください。(キャンバスの大きさは変わりません)