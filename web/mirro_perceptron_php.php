<?php
// Mirro on PHP: tiny single-neuron perceptron (educational toy).
// Same spirit as Mirro's real perceptron in Python (scripts/algorithms.py),
// but a self-contained PHP companion. Run on any PHP server: php -S 127.0.0.1:8090

header('Content-Type: text/plain; charset=utf-8');

function sigmoid(float $x): float { return 1.0 / (1.0 + exp(-$x)); }

function predict(array $w, float $b, array $x): float {
    $z = $b;
    foreach ($w as $i => $wi) $z += $wi * $x[$i];
    return sigmoid($z);
}

// AND-gate dataset: input[2] -> label (0 or 1)
$data = [
    [[0, 0], 0], [[0, 1], 0], [[1, 0], 0], [[1, 1], 1],
];

$w = [0.0, 0.0]; $b = 0.0; $lr = 0.5;
$epochs = 20;

echo "Mirro on PHP - tiny perceptron, learning AND-gate\n";
echo "-----------------------------------------------\n";
for ($e = 0; $e < $epochs; $e++) {
    $err = 0.0;
    foreach ($data as $sample) {
        [$x, $y] = $sample;
        $o = predict($w, $b, $x);
        $d = $o - $y;                       // delta
        $err += $d * $d;
        foreach ($w as $i => $wi) $w[$i] -= $lr * $d * $x[$i];
        $b -= $lr * $d;
    }
    if ($e === $epochs - 1 || $e % 5 === 0) {
        printf("epoch %2d  err=%.5f  w=[%.3f, %.3f]  b=%.3f\n", $e, $err, $w[0], $w[1], $b);
    }
}
echo "-----------------------------------------------\n";
$ok = 0;
foreach ($data as $sample) {
    [$x, $y] = $sample;
    $o = predict($w, $b, $x);
    $pred = $o > 0.5 ? 1 : 0;
    $ok += ($pred === $y) ? 1 : 0;
    printf("and(%d,%d) -> %.3f  pred=%d  real=%d\n", $x[0], $x[1], $o, $pred, $y);
}
printf("accuracy: %d/4\n", $ok);
echo "Real Mirro lives in Python (2.8M examples). This is her PHP echo. :)\n";