<?php
// Mirro on PHP - thin web wrapper around the live Mirro OpenAI-compatible API.
// Requires: PHP 7.4+, allow_url_fopen or cURL, and a running Mirro core
// (mirro_launcher.pyw / core/mirro_core.py on 127.0.0.1:3443).
// Now with chat history (SESSION) - Mirro remembers the conversation.

session_start();

$API = 'http://127.0.0.1:3443/v1/chat/completions';
$MAX_HISTORY = 12;

if (!isset($_SESSION['chat'])) {
    $_SESSION['chat'] = []; // [ ['role'=>'user'|'assistant', 'content'=>...], ... ]
}

$prompt = isset($_POST['prompt']) ? trim($_POST['prompt']) : '';
$doClear = isset($_POST['clear']);

if ($doClear) {
    $_SESSION['chat'] = [];
    header('Location: ' . strtok($_SERVER['REQUEST_URI'], '?'));
    exit;
}

$err = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $prompt !== '') {
    $_SESSION['chat'][] = ['role' => 'user', 'content' => mb_substr($prompt, 0, 2000)];

    // build context from recent messages
    $recent = array_slice($_SESSION['chat'], -$MAX_HISTORY);
    $messages = array_map(function ($m) {
        return ['role' => $m['role'], 'content' => $m['content']];
    }, $recent);

    $payload = json_encode(['model' => 'mirro', 'messages' => $messages], JSON_UNESCAPED_UNICODE);

    if (function_exists('curl_init')) {
        $ch = curl_init($API);
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => $payload,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 60,
        ]);
        $raw = curl_exec($ch);
        curl_close($ch);
    } else {
        $ctx = stream_context_create(['http' => [
            'method'  => 'POST',
            'header'  => "Content-Type: application/json\r\n",
            'content' => $payload,
            'timeout' => 60,
        ]]);
        $raw = @file_get_contents($API, false, $ctx);
    }

    if ($raw === false || $raw === '') {
        $err = 'Сервер Мирро не отвечает. Запусти mirro_launcher.pyw (127.0.0.1:3443) и попробуй ещё раз.';
        array_pop($_SESSION['chat']); // don't keep a user question without an answer
    } else {
        $data = json_decode($raw, true);
        $answer = isset($data['choices'][0]['message']['content'])
            ? $data['choices'][0]['message']['content']
            : '(Мирро вернула пустой ответ)';
        $_SESSION['chat'][] = ['role' => 'assistant', 'content' => mb_substr($answer, 0, 2500)];
    }
}
?>
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Мирро на PHP</title>
<style>
  *{box-sizing:border-box; margin:0; padding:0;}
  html,body{height:100%;}
  body{
    font-family:'Segoe UI',Verdana,sans-serif; color:#1e2a4a;
    background:linear-gradient(160deg,#eef4ff,#dbe9ff);
    display:flex; align-items:center; justify-content:center; padding:20px;
  }
  .card{max-width:680px; width:100%; background:#fff; border-radius:20px;
    padding:26px 24px; box-shadow:0 16px 46px rgba(80,90,160,.16);
    display:flex; flex-direction:column; gap:14px; max-height:92vh;}
  h1{font-size:24px;}
  .sub{color:#7a88ad; font-size:13px;}
  .chat{flex:1; overflow-y:auto; min-height:160px; display:flex;
    flex-direction:column; gap:8px; background:#f7faff; border:1px solid #dce5f6;
    border-radius:14px; padding:12px;}
  .m-user{align-self:flex-end; background:#e7efff; border:1px solid #c9d7f5;
    border-radius:12px 12px 4px 12px; padding:8px 12px; font-size:14px; max-width:85%;}
  .m-mirro{align-self:flex-start; background:#f3ecff; border:1px solid #decfff;
    border-radius:12px 12px 12px 4px; padding:8px 12px; font-size:14px; max-width:85%; white-space:pre-wrap;}
  textarea{width:100%; height:76px; resize:vertical; border:2px solid #d3ddf2;
    border-radius:12px; padding:10px 12px; font:inherit; color:inherit;}
  textarea:focus{outline:none; border-color:#4d7cfe;}
  .row{display:flex; gap:10px; align-items:center;}
  .btn{flex:none; padding:11px 24px; border:none; border-radius:999px;
    background:linear-gradient(135deg,#5b8bff,#845ef7); color:#fff; font-weight:700;
    font-size:15px; cursor:pointer;}
  .btn:active{transform:scale(.97);}
  .btn.gray{background:#eef3ff; color:#5a6a92;}
  .err{color:#b34040; font-weight:600;}
</style>
</head>
<body>
  <div class="card">
    <h1>Мирро на PHP 💙</h1>
    <div class="sub">тонкая обёртка: PHP &rarr; живой API Мирро (127.0.0.1:3443) · история в сессии · ядро не переписано</div>

    <div class="chat" id="chat">
      <?php if (empty($_SESSION['chat'])): ?>
        <div style="color:#aab6d4; align-self:center">Пока пусто — спроси у Мирро что-нибудь!</div>
      <?php else: ?>
        <?php foreach ($_SESSION['chat'] as $m): ?>
          <?php $cls = $m['role'] === 'user' ? 'm-user' : 'm-mirro'; ?>
          <div class="<?php echo $cls; ?>"><?php echo htmlspecialchars($m['content'], ENT_QUOTES, 'UTF-8'); ?></div>
        <?php endforeach; ?>
      <?php endif; ?>
    </div>

    <?php if ($err !== ''): ?>
      <div class="err"><?php echo htmlspecialchars($err, ENT_QUOTES, 'UTF-8'); ?></div>
    <?php endif; ?>

    <form method="post">
      <textarea name="prompt" placeholder="Спроси у Мирро что угодно..."></textarea>
      <div class="row">
        <button class="btn" type="submit">Спросить Мирро</button>
        <button class="btn gray" type="submit" name="clear" value="1">Очистить</button>
      </div>
    </form>
  </div>
  <script>
    var chat = document.getElementById('chat');
    if (chat) chat.scrollTop = chat.scrollHeight;
  </script>
</body>
</html>