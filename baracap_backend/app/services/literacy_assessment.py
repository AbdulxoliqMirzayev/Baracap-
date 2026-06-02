from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QuizOption:
    id: str
    text_uz: str
    text_ru: str
    correct: bool = False


@dataclass(frozen=True)
class QuizQuestion:
    id: str
    text_uz: str
    text_ru: str
    weight: int
    options: tuple[QuizOption, ...]


QUESTIONS: tuple[QuizQuestion, ...] = (
    QuizQuestion(
        id="q1",
        text_uz="Oylik daromad kelganda moliyaviy tartibni boshlash uchun eng to'g'ri birinchi qadam qaysi?",
        text_ru="Какой первый шаг помогает выстроить финансовый порядок после получения ежемесячного дохода?",
        weight=10,
        options=(
            QuizOption("a", "Daromadni ehtiyoj, majburiyat va jamg'armaga ajratish", "Разделить доход на потребности, обязательства и сбережения", True),
            QuizOption("b", "Oy oxirida qancha qolsa, shuni jamg'arish", "Откладывать только то, что останется в конце месяца"),
            QuizOption("c", "Avval barcha istak xaridlarini qilish", "Сначала оплатить все желаемые покупки"),
        ),
    ),
    QuizQuestion(
        id="q2",
        text_uz="Favqulodda jamg'arma nima uchun shaxsiy moliyada muhim hisoblanadi?",
        text_ru="Почему резервный фонд важен в личных финансах?",
        weight=15,
        options=(
            QuizOption("a", "Kutilmagan xarajatlarda qarz yoki kreditga qaram bo'lmaslik uchun", "Чтобы при неожиданных расходах не зависеть от долгов или кредитов", True),
            QuizOption("b", "Faqat daromad oshganda sarflash uchun", "Чтобы тратить его только после роста дохода"),
            QuizOption("c", "Investitsiya riskini butunlay yo'q qilish uchun", "Чтобы полностью убрать инвестиционный риск"),
        ),
    ),
    QuizQuestion(
        id="q3",
        text_uz="Kredit olishdan oldin qaysi ko'rsatkich qaror qabul qilishda eng muhim?",
        text_ru="Какой показатель наиболее важен перед оформлением кредита?",
        weight=15,
        options=(
            QuizOption("a", "Faqat reklamada yozilgan oylik to'lov", "Только ежемесячный платеж из рекламы"),
            QuizOption("b", "Umumiy qaytariladigan summa, foiz va qo'shimcha to'lovlar", "Общая сумма возврата, проценты и дополнительные платежи", True),
            QuizOption("c", "Kredit qancha tez berilishi", "Скорость выдачи кредита"),
        ),
    ),
    QuizQuestion(
        id="q4",
        text_uz="Agar inflyatsiya 12%, omonat daromadi 8% bo'lsa, pulning real qiymati haqida qaysi xulosa to'g'ri?",
        text_ru="Если инфляция 12%, а доходность вклада 8%, какой вывод о реальной стоимости денег верный?",
        weight=18,
        options=(
            QuizOption("a", "Nominal pul ko'payishi mumkin, lekin xarid quvvati pasayadi", "Номинально сумма может вырасти, но покупательная способность снизится", True),
            QuizOption("b", "Real daromad har doim 8% bo'ladi", "Реальная доходность всегда будет 8%"),
            QuizOption("c", "Inflyatsiya omonat qiymatiga ta'sir qilmaydi", "Инфляция не влияет на стоимость вклада"),
        ),
    ),
    QuizQuestion(
        id="q5",
        text_uz="Investitsiya portfelida diversifikatsiya nima uchun zarur?",
        text_ru="Зачем нужна диверсификация в инвестиционном портфеле?",
        weight=20,
        options=(
            QuizOption("a", "Bitta aktiv yomonlashsa, butun kapitalga ta'sirni kamaytirish uchun", "Чтобы снизить влияние одного неудачного актива на весь капитал", True),
            QuizOption("b", "Har qanday investitsiyani kafolatli foydaga aylantirish uchun", "Чтобы превратить любую инвестицию в гарантированную прибыль"),
            QuizOption("c", "Faqat qisqa muddatda tez foyda olish uchun", "Только для быстрой краткосрочной прибыли"),
        ),
    ),
    QuizQuestion(
        id="q6",
        text_uz="Uzoq muddatli maqsad uchun professional moliyaviy reja qaysi elementlarni o'z ichiga olishi kerak?",
        text_ru="Какие элементы должен включать профессиональный финансовый план для долгосрочной цели?",
        weight=22,
        options=(
            QuizOption("a", "Maqsad summasi, muddat, oylik depozit, risk chegarasi va qayta ko'rib chiqish jadvali", "Сумму цели, срок, ежемесячный взнос, границу риска и график пересмотра", True),
            QuizOption("b", "Faqat maqsad nomi va taxminiy summani", "Только название цели и примерную сумму"),
            QuizOption("c", "Pul yetmay qolsa, keyin reja tuzishni", "Составлять план только тогда, когда денег уже не хватает"),
        ),
    ),
)


def normalize_language(language: str | None) -> str:
    return "ru" if language == "ru" else "uz"


def public_questions(language: str = "uz") -> list[dict[str, object]]:
    language = normalize_language(language)
    return [
        {
            "id": question.id,
            "text": question.text_ru if language == "ru" else question.text_uz,
            "options": [
                {
                    "id": option.id,
                    "text": option.text_ru if language == "ru" else option.text_uz,
                }
                for option in question.options
            ],
        }
        for question in QUESTIONS
    ]


def score_answers(answers: dict[str, str]) -> int:
    score = 0
    for question in QUESTIONS:
        selected = answers.get(question.id)
        correct_option = next(option for option in question.options if option.correct)
        if selected == correct_option.id:
            score += question.weight
    return score


def level_for_score(score: int, language: str = "uz") -> str:
    language = normalize_language(language)
    if score >= 80:
        return "Высокий уровень" if language == "ru" else "Yuqori daraja"
    if score >= 50:
        return "Средний уровень" if language == "ru" else "O'rta daraja"
    return "Начальный уровень" if language == "ru" else "Boshlang'ich daraja"


def guide_type_for_score(score: int) -> str:
    return "professional" if score >= 50 else "simple"
