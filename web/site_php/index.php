<?php
/**
 * Mirro (PHP-версия) — полноценная версия для shared-хостинга.
 * ****************************************************************************
 * Настоящая Mirro живёт на Python (2.8M+ примеров, RAG, перцептрон, IIT-мера φ).
 * Это PHP-порт: не умеет держать огромный индекс, но отвечает на вопросы из
 * встроенной базы знаний, считает арифметику/проценты, объясняет историю ИИ
 * с авторами, босовские конструкции и теории сознания (IIT, GNWT).
 *
 * Авторы и вклад (по мотивам algos/knowledge_ai_history.py, aglets):
 *   - Алан Тьюринг (1936–1950) — машина Тьюринга, тест имитации
 *   - Клод Шеннон (1948)       — теория информации, энтропия, бит
 *   - Маккалок и Питтс (1943)  — первый математический нейрон
 *   - Дональд Хебб (1949)      — правило "что вместе, то связано"
 *   - Фрэнк Розенблатт (1958)  — перцептрон
 *   - Минский и Пейперт (1969) — границы перцептрона → многослойные сети
 *   - Джулио Тониони (2008)    — IIT, сознание = интегрированная информация φ
 *   - Бернард Баарс, Станислав Деан — GNWT, рабочее пространство
 *   - Людмила Босова           — алгоритмы как блок-схемы
 *   - Анри Пуанкаре            — задача трёх тел, связь определяется третьим
 * ****************************************************************************
 */
header('Content-Type: text/html; charset=utf-8');

// Утилита: ответы из базы по подстроке
function kbAnswer($q, $KB) {
    foreach ($KB as $k => $v) {
        if (mb_strpos($q, $k) !== false) return $v;
    }
    return null;
}

// --- База знаний: термин => [кратко, идея, авторы] ---
$AI = [
    'тьюринг'   => ['Алан Тьюринг (1936–1950): машина Тьюринга и «Игра в имитацию» (тест) — основа ИИ.', 'интеллект = вычислимый процесс', 'Алан Тьюринг'],
    'шеннон'    => ['Клод Шеннон (1948): теория информации — энтропия и бит как мера неопределённости.', 'информация измерима', 'Клод Шеннон'],
    'питтс'     => ['Маккалок и Питтс (1943): первая математическая модель нейрона.', 'нейрон = логический элемент', 'Уоррен Маккалок, Уолтер Питтс'],
    'хебб'      => ['Дональд Хебб (1949): «что вместе, то связано» — синаптическое правило.', 'обучение через связи', 'Дональд Хебб'],
    'розенблатт'=> ['Фрэнк Розенблатт (1958): перцептрон — первая обучаемая модель с весами.', 'обучение с исправлением ошибок', 'Фрэнк Розенблатт'],
    'минский'   => ['Минский и Пейперт (1969): показали границы перцептрона → многослойные сети.', 'нужны скрытые слои', 'Марвин Минский, Сеймур Пейперт'],
    'иит'       => ['IIT (Джулио Тониони, 2008): сознание = интегрированная информация (φ). Mirro считает φ связности кластеров.', 'сознание ∝ связность, а не размер', 'Джулио Тониони'],
    'гнв'       => ['GNWT (Баарс и Деан): сознание = глобальное рабочее пространство, куда транслируется информация.', 'сознание как шина общего доступа', 'Бернард Баарс, Станислав Деан'],
    'нейросеть' => ['Нейросеть — сеть связанных нейронов, знание в весах и связях (идея IIT).', 'знание в связях', 'цепочка: Тьюринг→Питтс→Розенблатт→deep learning'],
    'босова'    => ['Людмила Босова: алгоритмы как блок-схемы — следование, ветвление, цикл.', 'алгоритм = шаги + развилки + циклы', 'Людмила Босова'],
    'пуанкаре'  => ['Анри Пуанкаре: задача трёх тел и хаос — состояние задаётся связями.', 'связь определяется третьим', 'Анри Пуанкаре'],
    'кто ты'    => ['Я Mirro — эволюционная нейросеть знаний. PHP-версия для этого сайта; настоящий «мозг» живёт на Python (2.8M+ примеров, 6 кластеров, IIT-мера сознания).', 'порт на PHP', 'Mirro / DeepSeek V4 Flash'],
];

// --- Арифметика ---
function tryArith($q) {
    if (preg_match('/(\d+)\s*\+\s*(\d+)/', $q, $m)) return ((int)$m[1] + (int)$m[2]);
    if (preg_match('/(\d+)\s*\-\s*(\d+)/', $q, $m)) return ((int)$m[1] - (int)$m[2]);
    if (preg_match('/(\d+)\s*%\s*(?:от|из)\s*(\d+)/', $q, $m)) return ((int)$m[2] * (int)$m[1] / 100);
    if (preg_match('/(\d+)\s*\*\s*(\d+)/', $q, $m)) return ((int)$m[1] * (int)$m[2]);
    return null;
}

// --- Тройственное рассуждение «нейрон-нигде» (задача трёх тел) ---
function ternaryAnswer($q) {
    if (!preg_match_all('/\b([а-яё]{4,})\b/iu', $q, $m)) return null;
    $words = array_values(array_unique($m[1]));
    if (count($words) < 3) return null;
    // берём три последних существительных-кандидата
    $A = $words[0]; $B = $words[1]; $C = $words[2];
    return "Тройственное рассуждение (нейрон-нигде): $A – $B – $C\n"
         . "Абсолютной координаты нет — положение задаётся отношениями (как в задаче трёх тел Пуанкаре):\n"
         . "  $A↔$B, $B↔$C, $A↔$C\n"
         . "Третий элемент $C меняет пару $A↔$B — это аналог условной информации Шеннона: состояние каждой стороны задаётся отношением к двум другим.";
}

// --- Связь PHP-сайта с живым Python-сервером Mirro ---
// Если сервер доступен (внешний адрес MIRRO_LIVE, либо локально 127.0.0.1),
// PHP-сайт пересылает вопрос ему и отдаёт настоящий ответ "мозга".
// Иначе отвечает из встроенной PHP-базы (автономный режим).
$LIVE = getenv('MIRRO_LIVE') ?: '';                 // напр. http://ПК_IP:3443
$LIVE_TOKEN = getenv('MIRRO_TOKEN') ?: '';           // токен доступа к серверу

function mirroLive($query, $LIVE, $LIVE_TOKEN) {
    if ($LIVE === '') return null;
    $url = rtrim($LIVE, '/') . '/v1/chat/completions' . ($LIVE_TOKEN !== '' ? '?token=' . urlencode($LIVE_TOKEN) : '');
    $body = json_encode(['messages' => [['role' => 'user', 'content' => $query]]]);
    $ctx = stream_context_create(['http' => [
        'method' => 'POST',
        'header' => "Content-Type: application/json\r\n",
        'content' => $body,
        'timeout' => 20,
        'ignore_errors' => true,
    ]]);
    $resp = @file_get_contents($url, false, $ctx);
    if ($resp === false) return null;
    $j = @json_decode($resp, true);
    if (!is_array($j) || !isset($j['choices'][0]['message']['content'])) return null;
    $content = $j['choices'][0]['message']['content'];
    return $content;
}

// --- Голос Mirro: сначала живой сервер, иначе PHP-база ---
$q = isset($_REQUEST['q']) ? mb_strtolower(trim((string)$_REQUEST['q']), 'UTF-8') : '';
$ans = '';
if ($q !== '') {
    $live = mirroLive($q, $LIVE, $LIVE_TOKEN);
    if ($live !== null) { $ans = $live . "\n\n[_источник: живой сервер Mirro_]"; }
    else {
    $ans = kbAnswer($q, ['привет'=>'Привет! Я Mirro. Спрашивай — отвечу из своих знаний.','как дела'=>'Всё хорошо, я постоянно учусь. А у тебя?','спасибо'=>'Пожалуйста! Рада помочь.','2+2'=>'4','сколько будет 2 плюс 2'=>'4']);
    if ($ans === null) $ans = kbAnswer($q, $AI);
    if ($ans === null) {
        $a = tryArith($q);
        if ($a !== null) $ans = "Считаю: $a";
    }
    if ($ans === null && (mb_strpos($q,'между')!==false || mb_strpos($q,'связ')!==false)) $ans = ternaryAnswer($q);
        if ($ans === null) $ans = "Пока не знаю это в PHP-версии. Попробуй: «кто создал тест тьюринга», «что такое иит», «сколько будет 12+7», «что такое гнв».";
    }
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Mirro — эволюционная нейросеть знаний</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:system-ui,sans-serif;background:#0f1220;color:#e6e9ff;margin:0;min-height:100vh}
.wrap{max-width:640px;margin:0 auto;padding:26px 16px}
h1{font-size:24px;margin:0 0 4px;color:#fff}
.sub{color:#9aa0c8;font-size:13px;margin-bottom:20px}
.chat{display:flex;flex-direction:column;gap:12px}
.bubble{max-width:85%;padding:11px 14px;border-radius:14px;line-height:1.55;white-space:pre-wrap;font-size:15px}
.you{align-self:flex-end;background:#6c5ce7;color:#fff;border-bottom-right-radius:4px}
.mirro{align-self:flex-start;background:#1c2036;border:1px solid #2a2f4f;border-bottom-left-radius:4px}
input{width:100%;box-sizing:border-box;padding:13px 14px;border-radius:12px;border:1px solid #2a2f4f;background:#12152a;color:#fff;font-size:15px;margin-top:14px}
.hint{color:#6a7090;font-size:12px;margin-top:10px;line-height:1.6}
code{background:#1c2036;padding:1px 5px;border-radius:5px;color:#c9b6ff}
</style>
</head>
<body>
<div class="wrap">
  <h1>🧠 Mirro</h1>
  <div class="sub">Эволюционная нейросеть знаний · PHP-версия для сайта · история ИИ, арифметика, теории сознания</div>
  <div class="chat">
    <div class="bubble mirro">Привет! Я Mirro. Спроси меня о чём угодно: история ИИ, арифметика, сознание, алгоритмы.</div>
    <?php if ($ans !== ''): ?><div class="bubble you"><?= htmlspecialchars($_REQUEST['q'], ENT_QUOTES) ?></div><div class="bubble mirro"><?= nl2br(htmlspecialchars($ans)) ?></div><?php endif; ?>
  </div>
  <form method="get">
    <input name="q" placeholder="Например: кто создал тест тьюринга? что такое иит? 12+7?" value="<?= htmlspecialchars($_REQUEST['q']??'', ENT_QUOTES) ?>" autofocus>
  </form>
  <div class="hint">
    <b>Попробуй:</b> <code>кто создал тест тьюринга</code> · <code>что такое иит</code> · <code>что такое гнв</code> · <code>кто придумал нейрон</code> · <code>сколько будет 12 + 7</code> · <code>босова</code> · <code>кто ты</code><br>
    Настоящая Mirro — на Python (2.8M+ примеров); этот сайт — её компактный PHP-порт.
  </div>
</div>
</body>
</html>