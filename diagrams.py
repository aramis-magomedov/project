# import matplotlib.pyplot as plt 
# from io import BytesIO
# from aiogram import types, Router, F
# from aiogram.types import InputFile 

# router = Router()

# async def create_pie_chart(labels, sizes, title='Круговая диаграмма'):
#     # 1. Создаём фигуру и оси (subplot)
#     fig, ax = plt.subplots()  

#     # 2. Рисуем круговую диаграмму:
#     ax.pie(
#         sizes,               # данные (проценты или значения)
#         labels=labels,       # подписи секторов
#         autopct='%1.1f%%',   # формат отображения процентов (1.1 — одна цифра после запятой)
#         shadow=True,         # тень для красоты
#         startangle=90        # начальный угол (90 = сверху)
#     )
    
#     # 3. Делаем диаграмму круглой (без этого может быть овал)
#     ax.axis('equal')  
    
#     # 4. Устанавливаем заголовок
#     ax.set_title(title)  

#     # 5. Сохраняем график в буфер (оперативную память)
#     buf = BytesIO()  # создаём буфер
#     plt.savefig(buf, format='png')  # сохраняем в буфер как PNG
#     buf.seek(0)  # переводим указатель в начало буфера (чтобы потом прочитать)
#     plt.close()  # закрываем график, чтобы не накапливались в памяти
    
#     return buf  # возвращаем буфер с картинкой






# @router.message_handler(commands=['pie'])  # реагирует на команду /pie
# async def send_pie_chart(message: types.Message):
#     # 1. Подготавливаем данные для диаграммы
#     labels = ['Python', 'JavaScript', 'Java', 'C++', 'Other'] # названия секторов
#     sizes = [45, 30, 15, 7, 3]  # размеры секторов (могут быть любыми)
#     title = 'Распределение языков программирования'  # заголовок графика

#     # 2. Генерируем диаграмму (возвращается буфер с PNG)
#     chart = await create_pie_chart(labels, sizes, title)

#     # 3. Отправляем изображение пользователю
#     await message.answer_photo(
#         InputFile(chart, filename='pie_chart.png')  # создаём объект файла
#     )

#     # 4. Закрываем буфер (чтобы не было утечек памяти)
#     chart.close()