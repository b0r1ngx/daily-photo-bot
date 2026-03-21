1) Добавить поддержку больше языков (i18n):
1. Hindi, Modern Standard Arabic, Bahasa (Malaysia), Bengali
2. French, Italian, German

2) К присылаемым фоткам добавить инфу из фотки АПИ:
2.1) в ссылке иногда бывает полезная информация, например: https://unsplash.com/photos/a-colorful-parrot-peeks-through-green-leaves-FO74BlyGXXA -> a-colorful-parrot-peeks-through-green-leaves)
2.2) Location: Edward Youde Aviary, Kennedy Road, Central, Hong Kong
2.3) Camera: SONY, ILCE-7CR
2.4) может когда-то что-то еще (но это уже перебор, + иногда нет ни Location, ни Camera, fallback msg: "не указано автором" (не забудь перевести фразу на все языки))

Давать возможность пользователю настраивать, какая информация будет слаться вместе с фото

3) Посмотреть кто пользовался ботом (через БД, посмотреть что за инфу собираем). Do we gather any statistics about users? What is this info and what we can see now?
3.1) Do we log info what is user clicked? Do we log info about that we send a photo to a user? (To later understand or identify the issue)

4) Создать группу аналитику в которую будем слать инфу 1 раз в день, сколько на данный момент пользуется ботом, сколько новых пользователей, сколько всего отослали фото за день
5) Дать возможность смотреть текущее расписание, третья кнопка в сообщение которое выходит при клике на My Topics (Schedule (add this button) | Rename | Delete)

6) Resolve bug, after I 1 time click My Topics, then i don't get a message by clicking on any reply markup keyboard buttons (lets make it like this: we can start conversation via: 
6.1) /start, 
6.2) Any buttons that in reply markup keyboard, 

7) Why the user @b0r1ngx (it’s me) stop getting images?