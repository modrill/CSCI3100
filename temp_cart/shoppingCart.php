<?php
$host = '1234';
$dbname = 'yythaoye';
$user = 'taotao';
$pass = '123456';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8", $user, $pass);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("connection failed: " . $e->getMessage());
}
function getSessionId() {
    if (!isset($_COOKIE['cart_session'])) {
        $sessionId = bin2hex(random_bytes(16));
        setcookie('cart_session', $sessionId, time() + (86400 * 30), "/");
        return $sessionId;
    }
    return $_COOKIE['cart_session'];
}
?>

<?php
require '../config/db.php';

try {
    $stmt = $pdo->query("SELECT * FROM products");
    $products = $stmt->fetchAll(PDO::FETCH_ASSOC);
    
    header('Content-Type: application/json');
    echo json_encode($products);
} catch (PDOException $e) {
    http_response_code(500);
    echo json_encode(['error' => 'cannot get products']);
    error_log($e->getMessage());
}
?>

