(function () {
  const API = "/api";
  const LANG_KEY = "baracap_literacy_language";
  const RESULT_KEY = "baracap_literacy_result";
  const TELEGRAM_CHANNEL_URL = "https://t.me/BeTraderuzb";
  const app = document.getElementById("app");
  const toastEl = document.getElementById("toast");

  const COPY = {
    uz: {
      brandSubtitle: "Moliyaviy savodxonlik testi",
      headerBadge: "6 savol / 100 ball",
      giftPill: "Sovg'ali test",
      heroTitle: "Savollarga javob bering va sovg'amizni qo'lga kiriting",
      heroLead: "6 ta professional moliyaviy savodxonlik savoliga javob bering. Natija yakunda 100 ballik tizimda hisoblanadi va darajangizga mos sovg'a beriladi.",
      firstName: "Ism",
      lastName: "Familiya",
      phone: "Telefon raqami",
      status: "Holatingiz",
      choose: "Tanlang",
      statuses: [
        ["Talaba", "Talaba"],
        ["Ishlaydi", "Ishlaydi"],
        ["Tadbirkor", "Tadbirkor"],
        ["Ish qidirmoqda", "Ish qidirmoqda"],
        ["Boshqa", "Boshqa"],
      ],
      start: "Testni boshlash",
      visualTitle: "Moliyaviy darajangizni aniqlang",
      visualLead: "Birinchi 3 savol asosiy tushunchalarni, keyingi 3 savol esa professional moliyaviy qarorlarni tekshiradi.",
      steps: ["Ma'lumotlaringizni kiriting", "6 ta savolga javob bering", "Sovg'ani qo'lga kiriting"],
      quizTitle: "Moliyaviy savodxonlik testi",
      quizLead: "Savollarga diqqat bilan javob bering. Ballar faqat yakuniy natijada ko'rsatiladi.",
      answerCount: "javob",
      question: "savol",
      resultButton: "Natijani ko'rish",
      restart: "Boshidan boshlash",
      allRequired: "Iltimos, barcha savollarga javob bering",
      requestFailed: "So'rov bajarilmadi",
      result: "Natija",
      congrats: "Tabriklaymiz, sovg'ani qo'lga kiritdingiz",
      resultLead: "Ballingizga mos sovg'a tayyor. Tugmani bosing va sovg'ani qo'lga kiriting.",
      professionalGuide: "Sovg'ani qo'lga kiriting",
      simpleGuide: "Sovg'ani qo'lga kiriting",
      telegramSent: "Ma'lumotlaringiz Telegram botga yuborildi.",
      telegramFailed: "Telegramga yuborishda xatolik bo'ldi, lekin natijangiz hisoblandi.",
      telegramNotReady: "Telegram bot token va chat id .env ichida sozlanganda ma'lumot avtomatik yuboriladi.",
      downloadGuide: "Sovg'ani qo'lga kiriting",
      giftInfo: "Bizning sovg'amizda sizga kerakli moliyaviy savodxonlik uchun kerak bo'lgan kichik qo'llanma bor.",
      answerReview: "Savollar bo'yicha natija",
      yourAnswer: "Sizning javobingiz",
      correctAnswer: "To'g'ri javob",
      points: "Ball",
      correct: "To'g'ri",
      incorrect: "Noto'g'ri",
      newTest: "Yangi test",
    },
    ru: {
      brandSubtitle: "Тест финансовой грамотности",
      headerBadge: "6 вопросов / 100 баллов",
      giftPill: "Тест с подарком",
      heroTitle: "Ответьте на вопросы и получите наш подарок",
      heroLead: "Ответьте на 6 профессиональных вопросов по финансовой грамотности. Итог считается по 100-балльной системе, а подарок подбирается по вашему уровню.",
      firstName: "Имя",
      lastName: "Фамилия",
      phone: "Номер телефона",
      status: "Ваш статус",
      choose: "Выберите",
      statuses: [
        ["Студент", "Студент"],
        ["Работает", "Работает"],
        ["Предприниматель", "Предприниматель"],
        ["Ищет работу", "Ищет работу"],
        ["Другое", "Другое"],
      ],
      start: "Начать тест",
      visualTitle: "Определите свой финансовый уровень",
      visualLead: "Первые 3 вопроса проверяют базовые понятия, следующие 3 - профессиональные финансовые решения.",
      steps: ["Введите свои данные", "Ответьте на 6 вопросов", "Получите подарок"],
      quizTitle: "Тест финансовой грамотности",
      quizLead: "Отвечайте внимательно. Баллы показываются только в итоговом результате.",
      answerCount: "ответов",
      question: "вопрос",
      resultButton: "Показать результат",
      restart: "Начать заново",
      allRequired: "Пожалуйста, ответьте на все вопросы",
      requestFailed: "Запрос не выполнен",
      result: "Результат",
      congrats: "Поздравляем, вы получили подарок",
      resultLead: "Подарок подобран по вашему уровню. Нажмите кнопку, чтобы получить подарок.",
      professionalGuide: "Получите подарок",
      simpleGuide: "Получите подарок",
      telegramSent: "Ваши данные отправлены в Telegram-бот.",
      telegramFailed: "Не удалось отправить в Telegram, но результат рассчитан.",
      telegramNotReady: "После настройки Telegram bot token и chat id в .env данные будут отправляться автоматически.",
      downloadGuide: "Получить подарок",
      giftInfo: "В нашем подарке есть небольшое руководство, которое поможет улучшить вашу финансовую грамотность.",
      answerReview: "Результат по вопросам",
      yourAnswer: "Ваш ответ",
      correctAnswer: "Правильный ответ",
      points: "Баллы",
      correct: "Верно",
      incorrect: "Неверно",
      newTest: "Новый тест",
    },
  };

  const state = {
    participant: null,
    questions: [],
    answers: {},
  };

  function storageGet(key) {
    try {
      return window.localStorage.getItem(key);
    } catch {
      return null;
    }
  }

  function storageSet(key, value) {
    try {
      window.localStorage.setItem(key, value);
      return true;
    } catch {
      return false;
    }
  }

  function storageRemove(key) {
    try {
      window.localStorage.removeItem(key);
    } catch {
      // Ignore blocked storage; the in-memory state will still update.
    }
  }

  function lang() {
    return storageGet(LANG_KEY) === "ru" ? "ru" : "uz";
  }

  function copy() {
    return COPY[lang()] || COPY.uz;
  }

  function savedResult() {
    try {
      const result = JSON.parse(storageGet(RESULT_KEY) || "null");
      if (!result || typeof result !== "object") return null;
      if (!Number.isFinite(Number(result.score)) || !result.level) return null;
      return result;
    } catch {
      storageRemove(RESULT_KEY);
      return null;
    }
  }

  function setLanguage(next) {
    storageSet(LANG_KEY, next === "ru" ? "ru" : "uz");
    document.documentElement.lang = lang();
    syncChrome();
  }

  function syncChrome() {
    const c = copy();
    const brandSubtitle = document.getElementById("brandSubtitle");
    const headerBadge = document.getElementById("headerBadge");
    const langButton = document.querySelector("[data-action='language']");
    if (brandSubtitle) brandSubtitle.textContent = c.brandSubtitle;
    if (headerBadge) headerBadge.textContent = c.headerBadge;
    if (langButton) langButton.textContent = lang().toUpperCase();
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function toast(message, error = false) {
    if (!toastEl) return;
    toastEl.textContent = message;
    toastEl.classList.toggle("error", error);
    toastEl.classList.add("show");
    clearTimeout(toastEl._timer);
    toastEl._timer = setTimeout(() => toastEl.classList.remove("show"), 3200);
  }

  function setBusy(button, busy) {
    if (!button) return;
    button.disabled = busy;
  }

  async function api(path, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set("Accept", "application/json");
    if (options.body) headers.set("Content-Type", "application/json");
    let response;
    try {
      response = await fetch(`${API}${path}`, { ...options, headers });
    } catch {
      throw new Error(copy().requestFailed);
    }
    const text = await response.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = null;
    }
    if (!response.ok) {
      throw new Error(data?.detail || copy().requestFailed);
    }
    return data;
  }

  function giftSticker() {
    return `
      <div class="gift-sticker" aria-hidden="true">
        <div class="gift-icon"><span></span></div>
        <strong>${lang() === "ru" ? "Подарок" : "Sovg'a"}</strong>
      </div>
    `;
  }

  function scoreDiagram() {
    return `
      <div class="diagram" aria-hidden="true">
        <div class="score-ring"><span>100</span><small>${lang() === "ru" ? "балл" : "ball"}</small></div>
        <div class="diagram-caption">
          <b>6</b>
          <span>${lang() === "ru" ? "вопросов" : "savol"}</span>
        </div>
      </div>
    `;
  }

  function channelText() {
    return lang() === "ru" ? "Перейти в Telegram-канал" : "Telegram kanalga o'tish";
  }

  function launchCelebration() {
    const burst = document.createElement("div");
    burst.className = "celebration";
    burst.setAttribute("aria-hidden", "true");
    const colors = ["#c7ef61", "#7dd9d1", "#f0bc62", "#edf2ec"];
    for (let index = 0; index < 44; index += 1) {
      const particle = document.createElement("span");
      particle.style.setProperty("--x", `${Math.cos(index * 0.82) * (80 + (index % 9) * 11)}px`);
      particle.style.setProperty("--y", `${Math.sin(index * 1.04) * (70 + (index % 7) * 13)}px`);
      particle.style.setProperty("--delay", `${(index % 11) * 0.025}s`);
      particle.style.setProperty("--color", colors[index % colors.length]);
      burst.appendChild(particle);
    }
    document.body.appendChild(burst);
    window.setTimeout(() => burst.remove(), 1900);
  }

  function renderIntro() {
    const previousResult = savedResult();
    if (previousResult) {
      renderResult(previousResult, false);
      return;
    }

    const c = copy();
    app.innerHTML = `
      <div class="page">
        <section class="hero">
          <div class="panel hero-panel">
            <div class="hero-top">
              <span class="pill">${escapeHtml(c.giftPill)}</span>
              ${giftSticker()}
            </div>
            <h1>${escapeHtml(c.heroTitle).replace(lang() === "ru" ? "подарок" : "sovg'amizni", `<span class="accent">${lang() === "ru" ? "подарок" : "sovg'amizni"}</span>`)}</h1>
            <p class="lead muted">${escapeHtml(c.heroLead)}</p>
            <form id="participantForm" class="form-grid">
              <div class="field">
                <label>${escapeHtml(c.firstName)}</label>
                <input name="first_name" autocomplete="given-name" required minlength="2">
              </div>
              <div class="field">
                <label>${escapeHtml(c.lastName)}</label>
                <input name="last_name" autocomplete="family-name" required minlength="2">
              </div>
              <div class="field">
                <label>${escapeHtml(c.phone)}</label>
                <input name="phone" type="tel" inputmode="tel" autocomplete="tel" required minlength="7" placeholder="+998 90 123 45 67">
              </div>
              <div class="field">
                <label>${escapeHtml(c.status)}</label>
                <select name="status" required>
                  <option value="">${escapeHtml(c.choose)}</option>
                  ${c.statuses.map((item) => `<option value="${escapeHtml(item[0])}">${escapeHtml(item[1])}</option>`).join("")}
                </select>
              </div>
              <div class="button-row" style="grid-column:1/-1">
                <button class="primary" type="submit">${escapeHtml(c.start)}</button>
              </div>
            </form>
          </div>
          <aside class="info-visual">
            <div>
              <span class="pill">BARACAP</span>
              <h2>${escapeHtml(c.visualTitle)}</h2>
              <p class="muted">${escapeHtml(c.visualLead)}</p>
            </div>
            ${scoreDiagram()}
            <div class="steps">
              ${c.steps.map((step, index) => `<div class="step" style="--i:${index}"><b>${index + 1}</b><span>${escapeHtml(step)}</span></div>`).join("")}
            </div>
          </aside>
        </section>
      </div>
    `;
  }

  async function startQuiz(form) {
    if (savedResult()) {
      renderResult(savedResult(), false);
      return;
    }

    state.participant = Object.fromEntries(new FormData(form).entries());
    const data = await api(`/literacy-assessment/questions?language=${lang()}`);
    if (!Array.isArray(data?.questions) || !data.questions.length) {
      throw new Error(copy().requestFailed);
    }
    state.questions = data.questions;
    state.answers = {};
    renderQuiz();
  }

  function renderQuiz() {
    const c = copy();
    const answered = Object.keys(state.answers).length;
    const percent = Math.round((answered / state.questions.length) * 100);
    app.innerHTML = `
      <div class="page">
        <section class="panel">
          <span class="pill">${answered}/${state.questions.length} ${escapeHtml(c.answerCount)}</span>
          <h1 class="quiz-title">${escapeHtml(c.quizTitle)}</h1>
          <p class="muted">${escapeHtml(c.quizLead)}</p>
          <div class="progress" aria-label="Progress"><span style="width:${percent}%"></span></div>
        </section>
        <form id="quizForm" class="questions">
          ${state.questions.map((question, index) => questionMarkup(question, index)).join("")}
          <div class="button-row">
            <button class="primary" type="submit">${escapeHtml(c.resultButton)}</button>
            <button class="ghost" type="button" data-action="restart">${escapeHtml(c.restart)}</button>
          </div>
        </form>
      </div>
    `;
  }

  function questionMarkup(question, index) {
    const c = copy();
    return `
      <section class="question-card" style="--i:${index}">
        <div class="question-head">
          <div>
            <small>${index + 1}-${escapeHtml(c.question)}</small>
            <h3>${escapeHtml(question.text)}</h3>
          </div>
        </div>
        <div class="options">
          ${question.options.map((option) => `
            <label class="option">
              <input type="radio" name="${escapeHtml(question.id)}" value="${escapeHtml(option.id)}" ${state.answers[question.id] === option.id ? "checked" : ""} required>
              <span>${escapeHtml(option.text)}</span>
            </label>
          `).join("")}
        </div>
      </section>
    `;
  }

  async function submitQuiz(form) {
    if (savedResult()) {
      renderResult(savedResult(), false);
      return;
    }

    const formData = new FormData(form);
    state.answers = Object.fromEntries(formData.entries());
    if (Object.keys(state.answers).length !== state.questions.length) {
      toast(copy().allRequired, true);
      return;
    }
    const result = await api("/literacy-assessment", {
      method: "POST",
      body: JSON.stringify({
        participant: state.participant,
        answers: state.answers,
        language: lang(),
      }),
    });
    storageSet(RESULT_KEY, JSON.stringify(result));
    renderResult(result);
  }

  function renderResult(result, celebrate = true) {
    const c = copy();
    const score = Number.isFinite(Number(result?.score)) ? Number(result.score) : 0;
    const level = result?.level || "";
    app.innerHTML = `
      <section class="result-card">
        <span class="pill" style="margin:0 auto">${escapeHtml(c.result)}</span>
        ${giftSticker()}
        <div class="result-score">${score}/100</div>
        <h2>${escapeHtml(c.congrats)}</h2>
        <p class="level-label">${escapeHtml(level)}</p>
        <p class="muted">${escapeHtml(c.resultLead)}</p>
        <div class="gift-box">
          <strong>${escapeHtml(c.downloadGuide)}</strong>
          ${result.guide_url ? `<a class="primary" href="${escapeHtml(result.guide_url)}" download data-action="gift-download">${escapeHtml(c.downloadGuide)}</a>` : `<span class="muted">${escapeHtml(c.resultLead)}</span>`}
          <p id="giftInfo" class="gift-note" hidden>${escapeHtml(c.giftInfo)}</p>
        </div>
        ${answerReviewMarkup(result.breakdown || [])}
        <div class="button-row" style="justify-content:center">
          <a class="ghost channel-link" href="${TELEGRAM_CHANNEL_URL}" target="_blank" rel="noopener noreferrer">${escapeHtml(channelText())}</a>
        </div>
      </section>
    `;
    if (celebrate) launchCelebration();
  }

  function answerReviewMarkup(items) {
    const c = copy();
    if (!items.length) return "";
    return `
      <section class="answer-review">
        <div class="review-head">
          <span class="pill">${escapeHtml(c.answerReview)}</span>
        </div>
        <div class="review-list">
          ${items.map((item, index) => `
            <article class="review-card ${item.is_correct ? "is-correct" : "is-incorrect"}" style="--i:${index}">
              <div class="review-card-top">
                <span class="review-index">${index + 1}</span>
                <strong>${escapeHtml(item.is_correct ? c.correct : c.incorrect)}</strong>
                <b>${escapeHtml(item.earned_points)}/${escapeHtml(item.max_points)} ${escapeHtml(c.points)}</b>
              </div>
              <h3>${escapeHtml(item.question)}</h3>
              <div class="review-answers">
                <p><span>${escapeHtml(c.yourAnswer)}</span>${escapeHtml(item.selected_answer)}</p>
                <p><span>${escapeHtml(c.correctAnswer)}</span>${escapeHtml(item.correct_answer)}</p>
              </div>
            </article>
          `).join("")}
        </div>
      </section>
    `;
  }

  document.addEventListener("pointerdown", (event) => {
    const button = event.target.closest("button, a.primary");
    if (!button || button.disabled) return;
    const rect = button.getBoundingClientRect();
    const ripple = document.createElement("span");
    ripple.className = "ripple";
    ripple.style.left = `${event.clientX - rect.left}px`;
    ripple.style.top = `${event.clientY - rect.top}px`;
    button.appendChild(ripple);
    setTimeout(() => ripple.remove(), 560);
  });

  document.addEventListener("change", (event) => {
    const input = event.target.closest("input[type='radio']");
    if (!input) return;
    state.answers[input.name] = input.value;
    const progress = document.querySelector(".progress span");
    if (progress) {
      progress.style.width = `${Math.round((Object.keys(state.answers).length / state.questions.length) * 100)}%`;
    }
  });

  document.addEventListener("click", (event) => {
    const action = event.target.closest("[data-action]")?.getAttribute("data-action");
    if (action === "restart") {
      state.participant = null;
      state.answers = {};
      renderIntro();
    }
    if (action === "language") {
      setLanguage(lang() === "uz" ? "ru" : "uz");
      storageRemove(RESULT_KEY);
      state.participant = null;
      state.questions = [];
      state.answers = {};
      renderIntro();
    }
    if (action === "gift-download") {
      const giftInfo = document.getElementById("giftInfo");
      if (giftInfo) giftInfo.hidden = false;
    }
  });

  document.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.target;
    const button = form.querySelector("button[type='submit']");
    setBusy(button, true);
    try {
      if (form.id === "participantForm") await startQuiz(form);
      if (form.id === "quizForm") await submitQuiz(form);
    } catch (error) {
      toast(error.message, true);
    } finally {
      setBusy(button, false);
    }
  });

  setLanguage(lang());
  renderIntro();
})();
