<?php
// Mirro on PHP - thin web wrapper around the Mirro OpenAI-compatible API.
// Requires: PHP 7.4+, allow_url_fopen (or cURL), and the running Mirro core
// (mirro_launcher.pyw / core/mirro_core.py, which listens on 127.0.0.1:3443).
// Nothing is rewritten: PHP just relays the prompt to the live Mirro API.

$API = 'http://127.0.0.1:3443/v1/chat/completions';

$answer = '';
$err = '';
$prompt = isset($_POST['prompt']) ? trim($_POST['prompt']) : '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $prompt !== '') {
    $payload = json_encode([
        'model'    => 'mirro',
        'messages' => [['role' => 'user', 'content' => $prompt]],
    ], JSON_UNESCAPED_UNICODE);

    if (function_exists('curl_init')) {
        $ch = curl_init($API);
        curl_setopt_array($ch, [
            CURLOPT_POST           => true,
            CURLOPT_POSTFIELDS     => $payload,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 45,
        ]);
        $raw = curl_exec($ch);
        curl_close($ch);
    } else {
        $ctx = stream_context_create(['http' => [
            'method'  => 'POST',
            'header'  => "Content-Type: application/json\r\n",
            'content' => $payload,
            'timeout' => 45,
        ]]);
        $raw = @file_get_contents($API, false, $ctx);
    }

    if ($raw === false || $raw === '') {
        $err = 'Сервер Мирро не отвечает. Запусти mirro_launcher.pyw (127.0.0.1:3443) и нажми «Спросить» ещё раз.';
    } else {
        $data = json_decode($raw, true);
        $answer = isset($data['choices'][0]['message']['content'])
            ? $data['choices'][0]['message']['content']
            : '(Мирро вернула пустой ответ)';
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
  .card{max-width:640px; width:100%; background:#fff; border-radius:20px;
    padding:26px 24px; box-shadow:0 16px 46px rgba(80,90,160,.16);}
  h1{font-size:24px; margin-bottom:4px;}
  .sub{color:#7a88ad; font-size:13px; margin-bottom:18px;}
  textarea{width:100%; height:88px; resize:vertical; border:2px solid #d3ddf2;
    border-radius:12px; padding:10px 12px; font:inherit; color:inherit;}
  textarea:focus{outline:none; border-color:#4d7cfe;}
  button{margin-top:10px; padding:11px 26px; border:none; border-radius:999px;
    background:linear-gradient(135deg,#5b8bff,#845ef7); color:#fff; font-weight:700;
    font-size:15px; cursor:pointer;}
  button:active{transform:scale(.97);}
  .err{color:#b34040; font-weight:600; margin-top:14px;}
  .out{margin-top:16px; background:#f3f7ff; border:1px dashed #b9c8ea;
    border-radius:14px; padding:14px 16px; line-height:1.65; white-space:pre-wrap;}
  .out b{color:#3b4a70;}
</style>
</head>
<body>
  <div class="card">
    <h1>Мирро на PHP 💙</h1>
    <div class="sub">тонкая обёртка: PHP &rarr; живой API Мирро (127.0.0.1:3443). Ядро не переписано, только мост.</div>

    <form method="post">
      <textarea name="prompt" placeholder="Спроси у Мирро что угодно..."><?php echo htmlspecialchars($prompt, ENT_QUOTES, 'UTF-8'); ?></textarea>
      <button type="submit">Спросить Мирро</button>
    </form>

    <?php if ($err !== ''): ?>
      <div class="err"><?php echo htmlspecialchars($err, ENT_QUOTES, 'UTF-8'); ?></div>
    <?php endif; ?>

    <?php if ($answer !== ''): ?>
      <div class="out"><b>Мирро:</b><br><?php echo htmlspecialchars($answer, ENT_QUOTES, 'UTF-8'); ?></div>
    <?php endif; ?>
  </div>
</body>
</html>