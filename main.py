from fastapi import FastAPI, File, UploadFile, HTTPException
import os

from parser.config import ParserConfig
from parser.parser import Parser
from parser.lint import duration_lint
from parser.transforms import duration_fixer

# Инициализируем FastAPI-приложение
app = FastAPI(title="StankinScheduleParser API")

# Создаём и настраиваем парсер (твоя конфигурация из main.py)
parser = Parser(
    config=ParserConfig(
        text_cleaners=(
            lambda t: t.replace('_Вакансия ', ''),
            lambda t: t.replace('С/З СТАНКИН 1', 'С/З СТАНКИН'),
            lambda t: t.replace('- ', '-'),
            lambda t: t.replace(' - ', '-'),
            lambda t: t.replace('- ', '-'),
            lambda t: t.replace(
                'Оборудование цифровых производств. Интегрированные роботизированные системы',
                'Оборудование цифровых производств, Интегрированные роботизированные системы'
            )
        ),
        pair_lints=(duration_lint,),
        pair_transforms=(duration_fixer,)
    )
)

@app.get("/")
async def root():
    return {"message": "Сервер запущен. Отправьте PDF на /parse"}

@app.post("/parse", summary="Загрузить PDF и получить JSON-расписание")
async def parse_schedule(file: UploadFile = File(...)):
    # Проверяем расширение
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Только PDF-файлы разрешены")
    # Сохраняем временный файл
    tmp_path = "temp_schedule.pdf"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())
    try:
        # Парсим PDF и возвращаем результат
        result = parser.parse_schedule(tmp_path, schedule_name=file.filename)
        return {"name": result.name, "pairs": result.pairs}
    except Exception as e:
        # В случае ошибки возвращаем 500
        raise HTTPException(500, f"Ошибка парсинга: {e}")
    finally:
        os.remove(tmp_path)

# Этот блок нужен для локального запуска (не критичен на Render)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
