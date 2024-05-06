import logging

import aiosqlite
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)

API_TOKEN = 'token'
router = Router()
bot = Bot(token=API_TOKEN)
dp = Dispatcher()


@router.message(Command(commands=['start']))
async def start(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect('users.db') as db:
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            user = await cursor.fetchone()
            if user:
                await process_message(message)
            else:
                await message.answer(
                    ("Привет!\n"
                     "Для начала знакомства пройди регистрацию"))
        await main_menu(message)


@router.message(Command(commands=['register']))
async def register(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect('users.db') as db:
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            user = await cursor.fetchone()
            if not user:
                keyboard = types.ReplyKeyboardMarkup(
                    keyboard=[[
                        types.KeyboardButton(
                            text='Я принимаю условия конфиденциальности'
                        ),
                        types.KeyboardButton(
                            text='Я не принимаю условия конфиденциальности'
                        ),
                        types.KeyboardButton(
                            text='Прочитать политику конфиденциальности'
                        )
                    ]],
                    one_time_keyboard=True
                )
                await message.answer(
                    "Пожалуйста, примите условия конфиденциальности:",
                    reply_markup=keyboard
                )
            else:
                await message.answer("Ты уже зарегистрирован.")
                await main_menu(message)


@router.message(Command(commands=['change_info']))
async def change_info(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect('users.db') as db:
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            user = await cursor.fetchone()
            if user:
                await db.execute(
                    "UPDATE users SET name = NULL, age = NULL, gender = NULL, "
                    + "preference = NULL, interests = NULL, media = NULL, "
                    + "media_type = NULL WHERE user_id = ?",
                    (user_id,)
                )
                await db.commit()
                await message.answer("Как тебя зовут?")


@router.message(lambda message: message.text in [
    "Я принимаю условия конфиденциальности",
    "Я не принимаю условия конфиденциальности",
    "Прочитать политику конфиденциальности"
])
async def handle_privacy_choice(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect('users.db') as db:
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            user = await cursor.fetchone()
            if not user:
                if message.text == ("Я принимаю условия"
                                    + " конфиденциальности"):
                    await db.execute(
                        "INSERT INTO users (user_id, privacy_accepted) VALUES "
                        + "(?, ?)", (user_id, True))
                    await db.commit()
                    await message.answer("Привет! Давай начнем регистрацию.\n"
                                         "Напиши свое имя:")
                elif message.text == ("Я не принимаю условия"
                                      " конфиденциальности"):
                    await message.answer(
                        "Вы не приняли условия конфиденциальности. "
                        "Но Вы всегда можете вернуться и продолжить!"
                    )
                    await main_menu(message)
                elif message.text == "Прочитать политику конфиденциальности":
                    await message.answer("""
Условия конфиденциальности

Сбор информации: Мы собираем только те данные,
которые вы предоставляете нам в процессе использования нашего бота.

Использование информации: Мы используем предоставленную вами информацию
только для оказания услуг, связанных с функционированием нашего бота,
в том числе для подбора подходящих пользователей для общения.

Хранение информации: Ваши персональные данные хранятся в
зашифрованном виде и недоступны для сторонних лиц.

Передача информации: Мы не передаем вашу персональную информацию
третьим лицам без вашего согласия, за исключением вашего nickname в Telegram.

Безопасность данных: Мы предпринимаем все необходимые меры для защиты ваших
данных от несанкционированного доступа или использования.

Отказ от ответственности: Мы не несем ответственности за действия
пользователей, которые могут получить доступ к вашей информации через наш бот.

Изменения в политике конфиденциальности: Мы оставляем за собой право вносить
изменения в нашу политику конфиденциальности. В случае внесения изменений,
мы уведомим вас об этом.

Согласие пользователя: Используя нашего бота, вы соглашаетесь с
нашей политикой конфиденциальности и соглашаетесь с ее условиями.""")
                    await main_menu(message)
            else:
                await message.answer("Вы уже зарегистрированы.")
                await main_menu(message)


async def send_user_info(message, user):
    user_id = message.from_user.id
    async with aiosqlite.connect('users.db') as db:
        async with db.execute(
            'SELECT * FROM users WHERE user_id = ?', (user_id,)
        ) as cursor:
            current_user = await cursor.fetchone()
            if current_user is not None:
                keyboard = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="Понравился",
                                callback_data=f"like_{user[0]}"
                            ),
                            types.InlineKeyboardButton(
                                text="Не понравился",
                                callback_data=f"dislike_{user[0]}")]])
                if isinstance(user[7], str):
                    if user[7] == types.ContentType.VIDEO:
                        await bot.send_video(
                            chat_id=message.chat.id, video=user[6]
                        )
                    elif user[7] == types.ContentType.PHOTO:
                        await bot.send_photo(
                            chat_id=message.chat.id, photo=user[6]
                        )
                no_contact = "Пользователь не оставил контактов"
                await message.answer(
                    f"Имя: {user[1]}\n"
                    f"Возраст: {user[2]}\n"
                    f"Пол: {user[3]}\n"
                    f"Интересы: {user[5]}\n"
                    f"Общих интересов: "
                    f"{count_interest_matches(current_user, user)}\n"
                    f"Контакты в Telegram: "
                    + f"{user[8] if user[8] else no_contact}",
                    reply_markup=keyboard)


@router.callback_query(
    lambda callback_query: callback_query.data.startswith(
        ('like_', 'dislike_')
    )
)
async def handle_like_dislike(callback_query: types.CallbackQuery):
    action, user_id = callback_query.data.split('_')
    user_id = int(user_id)
    current_user_id = callback_query.from_user.id

    async with aiosqlite.connect('users.db') as db:
        async with db.execute(
            'SELECT * FROM users WHERE user_id = ?', (current_user_id,)
        ) as cursor:
            current_user = await cursor.fetchone()
            if current_user is None:
                await callback_query.answer("Ошибка. Пользователь не найден.")
                return

        async with db.execute(
            'SELECT * FROM users WHERE user_id = ?', (user_id,)
        ) as cursor:
            user = await cursor.fetchone()
            if user is None:
                await callback_query.answer("Ошибка. Пользователь не найден.")
                return

        if action == 'like':
            await db.execute(
                'INSERT INTO favorites (user_id, favorite_user_id) VALUES '
                + '(?, ?)', (current_user_id, user_id)
            )
            await db.commit()
            await callback_query.answer(
                "Пользователь добавлен в понравившиеся!"
            )
        elif action == 'dislike':
            await db.execute(
                'DELETE FROM favorites WHERE user_id = ? AND favorite_user_id'
                + ' = ?',
                (current_user_id, user_id)
            )
            await db.commit()
            await callback_query.answer(
                "Пользователь не добавлен в понравившиеся."
            )


@router.message(Command(commands=['favorites']))
async def show_favorites(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect('users.db') as db:
        async with db.execute(
            'SELECT * FROM favorites WHERE user_id = ?', (user_id,)
        ) as fav_cursor:
            favorites = await fav_cursor.fetchall()
            if favorites:
                await message.answer("Пользователи, которые вам понравились:")
                for favorite in favorites:
                    favorite_id = favorite[1]
                    async with db.execute(
                        'SELECT * FROM users WHERE user_id = ?', (favorite_id,)
                    ) as fav_user_cursor:
                        favorite_user = await fav_user_cursor.fetchone()
                        if favorite_user:
                            await send_user_info(message, favorite_user)
            else:
                await message.answer(
                    "Ваш список понравившихся пользователей пока пуст."
                )
    await main_menu(message)


@router.message(Command(commands=['search']))
async def search(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect('users.db') as connection:
        current_user = await connection.execute(
            'SELECT * FROM users WHERE user_id = ?', (user_id,)
        )
        current_user = await current_user.fetchone()
        if current_user is not None:
            suitable_users = await find_suitable_users(current_user)
            if suitable_users:
                await message.answer(
                    "Вот некоторые пользователи, "
                    + "которые могут вас заинтересовать:"
                )
                for user in suitable_users:
                    await send_user_info(message, user)
            else:
                await message.answer(
                    "К сожалению, сейчас нет подходящих пользователей."
                )
        else:
            await message.answer(
                "Вы еще не зарегистрировались. "
                + "Используйте команду /register для регистрации."
            )
    await main_menu(message)


async def find_suitable_users(current_user):
    suitable_users = []
    async with aiosqlite.connect('users.db') as db:
        async with db.execute('SELECT * FROM users') as cursor:
            async for row in cursor:
                user = row
                if user[0] == current_user[0]:
                    continue
                if current_user[4] != user[3]:
                    if current_user[4] != 'Неважно':
                        continue
                if count_interest_matches(current_user, user) < 1:
                    continue
                suitable_users.append(user)
    return suitable_users


def count_interest_matches(current_user, other_user):
    current_user_interests = set(current_user[5].lower().split(', '))
    other_user_interests = set(other_user[5].lower().split(', '))

    matching_interests = current_user_interests & other_user_interests

    return len(matching_interests)


@router.message(Command(commands=['help']))
async def help_command(message: types.Message):
    help_text = (
        "Привет! Я бот знакомств.\n\n"
        "Я помогу тебе найти интересных людей для общения и знакомств!\n\n"
        "Для начала знакомства нажми /register и следуй инструкциям.\n\n"
        "Или можешь воспользоваться кнопками ниже:"
    )

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton(text='Давай!'),
                types.KeyboardButton(text='Не хочу!')
            ]
        ],
        one_time_keyboard=True
    )

    await message.answer(help_text, reply_markup=keyboard)


def create_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text='/register Регистрация')],
            [types.KeyboardButton(text='/change_info Изменить профиль')],
            [types.KeyboardButton(text='/search Поиск')],
            [types.KeyboardButton(text='/favorites Избранное')],
            [types.KeyboardButton(text='/help Помощь')]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    return keyboard


@router.message(Command(commands=['main']))
async def main_menu(message: types.Message):
    keyboard = create_main_keyboard()
    await message.answer("Главное меню:", reply_markup=keyboard)


@router.message()
async def process_message(message: types.Message):
    user_id = message.from_user.id

    async with aiosqlite.connect('users.db') as db:
        cursor = await db.cursor()

        await cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        existing_user = await cursor.fetchone()

        if existing_user:
            current_user = list(existing_user)
        else:
            current_user = None

        if current_user is None:
            if message.text == '/register':
                await message.answer(
                    "Привет! Для начала знакомства пройди "
                    + "регистрацию командой /register"
                )
            else:
                await message.answer(
                    "Вы еще не зарегистрировались. "
                    + "Используйте команду /register для регистрации."
                )
            return

        if current_user[1] is None:
            current_user[1] = message.text
            await message.answer("Сколько тебе лет?")

        elif current_user[2] is None:
            try:
                age = int(message.text)
                if age <= 0:
                    raise ValueError
                current_user[2] = age
                await message.answer(
                    "Теперь определимся с полом.",
                    reply_markup=types.ReplyKeyboardMarkup(
                        keyboard=[
                            [types.KeyboardButton(text='Девушка'),
                             types.KeyboardButton(text='Парень')]
                        ],
                        one_time_keyboard=True
                    )
                )
            except ValueError:
                await message.answer(
                    "Пожалуйста, введите корректный возраст "
                    + "(целое положительное число)."
                )
                return

        elif current_user[3] is None:
            current_user[3] = message.text
            await message.answer(
                "Кого ты ищешь?",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[
                        [types.KeyboardButton(text='Девушка'),
                         types.KeyboardButton(text='Парень'),
                         types.KeyboardButton(text='Неважно')]
                    ],
                    one_time_keyboard=True
                )
            )

        elif current_user[4] is None:
            current_user[4] = message.text
            await message.answer(
                "Расскажи о себе и кого хочешь найти, "
                + "чем предлагаешь заняться, укажи свои интересы через запятую.\n"
                "Это поможет лучше подобрать тебе компанию."
            )

        elif current_user[5] is None:
            current_user[5] = message.text
            await message.answer(
                "Теперь пришли фото или запиши видео (до 15 сек), "
                + "его будут видеть другие пользователи.\n"
                "Отправь готовое фото или видео."
            )

        elif message.content_type in [
            types.ContentType.PHOTO,
            types.ContentType.VIDEO
        ]:
            if current_user[6] is None:
                media = (message.photo[-1].file_id
                         if message.photo
                         else message.video.file_id)
                media_type = message.content_type
                current_user[6] = media
                current_user[7] = media_type
                current_user[8] = message.from_user.username
                await message.answer("Спасибо! Ваше фото/видео сохранено.")

                suitable_users = await find_suitable_users(current_user)
                if suitable_users:
                    await message.answer(
                        "Вот некоторые пользователи, "
                        + "которые могут вас заинтересовать:"
                    )
                    for user in suitable_users:
                        await send_user_info(message, user)
                else:
                    await message.answer(
                        "К сожалению, сейчас нет подходящих пользователей."
                    )
            else:
                await message.answer("Вы уже отправили фото/видео.")
        else:
            await message.answer("Пожалуйста, отправьте фото или видео.")

        current_user = tuple(current_user)

        await cursor.execute(
            "UPDATE users SET name=?, age=?, gender=?, preference=?, "
            + "interests=?, media=?, media_type=?, nickname=? WHERE user_id=?",
            (current_user[1], current_user[2], current_user[3],
             current_user[4], current_user[5], current_user[6],
             current_user[7], current_user[8], user_id))
        await db.commit()
        await cursor.close()


if __name__ == '__main__':
    dp.include_router(router)
    dp.run_polling(bot)
