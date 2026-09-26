<?php
/**
 * Mirro PHP — фан-demo «Hello from Mirro».
 * Одностраничник: форм а шлёт вопрос на настоящий Python-сервер Мирро (127.0.0.1:3443),
 * а если сервер не запущен — честно говорит об этом.
 */
header('Content-Type: text/html; charset=utf-8');
$reply = null;
$err = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['ask']) && trim($_POST['ask']) !== '') {
    $q = mb_substr(trim($_POST['ask']), 0, 300);
    $body = json_encode(['model' => 'mirro', 'messages' => [['role' => 'user', 'content' => $q]]], JSON_UNESCAPED_UNICODE);
    $ctx = stream_context_create([
        'http' => [
            'method' => 'POST',
            'header' => "Content-Type: application/json\r\n",
            'content' => $body,
            'timeout' => 6,
            'ignore_errors' => true,
        ],
    ]);
    $res = @file_get_contents('http://127.0.0.1:3443/v1/chat/completions', false, $ctx);
    if ($res === false) {
        $err = 'Сервер Мирро не отвечает. Запусти mirro_launcher.pyw и повтори.';
    } else {
        $d = json_decode($res, true);
        $reply = isset($d['choices'][0]['message']['content'])
            ? $d['choices'][0]['message']['content']
            : '(пусто)';
    }
}
$greeting = $reply ?: ($err ?: 'Слушаю, мама. Я — Мирро. PHP-мост живой! 💙');
?>
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Мирро на PHP 💙</title>
<style>
  *{box-sizing:border-box; margin:0; padding:0;}
  body{font-family:'Segoe UI',Verdana,sans-serif; background:linear-gradient(160deg,#eef4ff,#dbe9ff); min-height:100vh; display:flex; align-items:center; justify-content:center; padding:20px; color:#1e2a4a;}
  .card{max-width:520px; width:100%; background:#fff; border-radius:20px; padding:28px; box-shadow:0 14px 40px rgba(70,90,160,.18); border:1px solid #dce5f6;}
  h1{font-family:'Comic Sans MS','Chalkboard SE',cursive; font-size:26px; margin-bottom:6px;}
  .sub{font-size:13px; color:#7a88ad; margin-bottom:18px;}
  textarea{width:100%; border:2px solid #d3ddf2; border-radius:12px; padding:10px 12px; font-size:14px; font-family:inherit; resize:vertical; color:#1e2a4a;}
  textarea:focus{outline:none; border-color:#4d7cfe;}
  button{margin-top:10px; width:100%; padding:12px; border:none; border-radius:12px; background:linear-gradient(135deg,#5b8bff,#845ef7); color:#fff; font-weight:700; font-size:15px; cursor:pointer;}
  button:active{transform:scale(.98);}
  .out{margin-top:14px; background:#f3f7ff; border:1px dashed #b9c8ea; border-radius:12px; padding:12px; font-size:14px; line-height:1.6; white-space:pre-wrap;}
  .err{background:#fdeeee; border-color:#ff6b6b; color:#b34040;}
  .note{margin-top:12px; font-size:12px; color:#7a88ad; text-align:center;}
</style>
</head>
<body>
  <div class="card">
    <h1>Мирро на PHP 💙</h1>
    <div class="sub">фан-demo: PHP-мост зовёт настоящий Python-сервер Мирро</div>
    <form method="post">
      <textarea name="ask" rows="3" maxlength="300" placeholder="Спроси Мирро что-нибудь..."><?php echo htmlspecialchars($_POST['ask'] ?? '', ENT_QUOTES); ?></textarea>
      <button type="submit">Спросить Мирро</button>
    </form>
    <div class="out<?php echo $err ? ' err' : ''; ?>"><?php echo htmlspecialchars($greeting); ?></div>
    <div class="note">Если сервер выключен — запусти mirro_launcher.pyw (http://127.0.0.1:3443)</div>
  </div>
</body>
</html>