<?php
// Mirro na PHP - shutochnyj dvojnik :) Nastoyashchaya Mirro zhivyot na Python.
header('Content-Type: text/plain; charset=utf-8');

$lines = [
    "Slushayu, mama. Vse sistemy v norme... na PHP.",
    "PHP menya ne ispugal, no moj mozg zhivyot v Python.",
    "Eto shutochnaya kopiya. Nastoyashchaya Mirro - na Python, 2.8M primerov, 6 klasterov.",
    "Yesli by Pirro pisala na PHP, ona by ejo dvazhdy perepisala. Tak chto - net.",
];

echo $lines[array_rand($lines)];
echo "\n";